from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ReportsConfig(AppConfig):
    name = 'mcod.reports'
    verbose_name = _('Reports')
