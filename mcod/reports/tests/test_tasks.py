import datetime
import json
import os
from time import sleep
import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from django.conf import settings

from mcod.reports.models import SummaryDailyReport
from mcod.reports.tasks import generate_csv, create_daily_resources_report

User = get_user_model()
Report = apps.get_model('reports', 'Report')
TaskResult = apps.get_model('django_celery_results', 'TaskResult')


@pytest.mark.django_db
class TestTasks(object):
    def test_generate_csv(self, active_user, admin_user):
        request_date = datetime.datetime(2018, 12, 4)
        eager = generate_csv.s(
            [active_user.id, admin_user.id],
            User._meta.label,
            active_user.id,
            request_date.strftime('%Y%m%d%H%M%S.%s')
        ).apply_async(countdown=1)

        sleep(1)
        assert eager

        result_task = TaskResult.objects.get(task_id=eager)
        result_dict = json.loads(result_task.result)

        assert result_dict['model'] == 'users.User'
        assert 'date' in result_dict
        assert result_dict['user_email'] == active_user.email
        assert result_dict['csv_file'].startswith('/media/reports/users/')
        assert result_dict['csv_file'].endswith(request_date.strftime('%Y%m%d%H%M%S.%s') + '.csv')

        r = Report.objects.get(task=result_task)

        assert r.task == result_task
        assert r.task.status == 'SUCCESS'
        assert r.file == result_dict['csv_file']
        assert r.ordered_by == active_user
        assert r.model == 'users.User'
        file_path = os.path.join(settings.TEST_ROOT, result_dict['csv_file'].strip('/'))
        with open(file_path, 'r') as f:
            lines = f.readlines()

        assert len(lines) == 3
        for line in lines:
            assert len(line.split(';')) == 7

    def test_invalid_user_ordering_report(self, active_user):
        request_date = datetime.datetime.now()
        eager = generate_csv.delay(
            [active_user.id, ],
            User._meta.label,
            active_user.id + 100,
            request_date.strftime('%Y%m%d%H%M%S.%s')
        )

        assert eager
        result_task = TaskResult.objects.get(task_id=eager)
        r = Report.objects.get(task=result_task)
        assert r.task == result_task
        assert r.task.status == 'FAILURE'

    def test_wrong_model_report(self, active_user):
        request_date = datetime.datetime.now()
        eager = generate_csv.delay(
            [active_user.id],
            'users.WrongModel',
            active_user.id,
            request_date.strftime('%Y%m%d%H%M%S.%s')
        )

        assert eager
        result_task = TaskResult.objects.get(task_id=eager)
        r = Report.objects.get(task=result_task)
        assert r.task == result_task
        assert r.task.status == 'FAILURE'

    # def test_no_file_report(self, active_user):
    #     request_date = datetime.datetime.now()
    #     from mcod import settings
    #     bkp = settings.REPORTS_MEDIA_ROOT
    #     settings.REPORTS_MEDIA_ROOT = ""
    #     eager = generate_csv.delay(
    #         pks=[active_user.id],
    #         model_info=User._meta.label,
    #         user_id=active_user.id,
    #         request_date=request_date
    #     )
    #
    #     assert eager
    #     result_task = TaskResult.objects.get(task_id=eager)
    #     r = Report.objects.get(task=result_task)
    #     assert r.task == result_task
    #     assert r.task.status == 'FAILURE'
    #     FIXME na gitlabie jest SUCCESS
    #     settings.REPORTS_MEDIA_ROOT = bkp

    def test_create_daily_resources_report(self, admin_user, valid_resource):
        admin_user.id = 1
        admin_user.email = "testadmin@test.xx"
        admin_user.save()

        request_date = datetime.datetime.now().strftime('%Y_%m_%d_%H')
        create_daily_resources_report()
        r = SummaryDailyReport.objects.last()

        assert r
        assert r.file.startswith('media/reports/daily/Zbiorczy_raport_dzienny_')
        assert r.file.endswith('.csv')
        assert request_date in r.file
