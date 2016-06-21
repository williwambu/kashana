import re
from django.core.urlresolvers import reverse
from django.views.generic import CreateView, DetailView
from braces.views import LoginRequiredMixin, PermissionRequiredMixin
from appconf.models import Settings
from .api import ResultSerializer
from .mixins import AptivateDataBaseMixin
from .models import (
    Assumption, Indicator, LogFrame, Milestone, Result, RiskRating,
    SubIndicator, Target
)


class ResultEditor(LoginRequiredMixin, AptivateDataBaseMixin, DetailView):
    model = Result
    template_name = 'logframe/result.html'

    def get_logframe(self):
        return self.object.log_frame

    def get_data(self, logframe, data):
        """
        Get a dict containing all the data for one logframe
        """
        result = self.object
        data.update({
            'result': ResultSerializer(result).data,
            'riskratings': self._json_object_list(
                RiskRating.objects.all(),
                model_class=RiskRating),
            'assumptions': self._json_object_list(
                logframe.all_assumptions(),
                model_class=Assumption),
            'indicators': self.get_related_model_data(
                {'result': result},
                Indicator),
            'subindicators': self.get_related_model_data(
                {'indicator__result': result},
                SubIndicator),
            'targets': self.get_related_model_data(
                {'subindicator__indicator__result': result},
                Target),
            'milestones': self.get_related_model_data(
                {'log_frame': result.log_frame},
                Milestone),
        })
        return data


class ResultMonitor(LoginRequiredMixin, AptivateDataBaseMixin, DetailView):
    model = Result
    template_name = 'logframe/result.html'

    def get_logframe(self):
        return self.object.log_frame

    def get_data(self, logframe, data):
        """
        Get a dict containing all the data for one logframe
        """
        data.update({
            'result': ResultSerializer(self.object).data,
        })
        return data


class CreateLogframe(PermissionRequiredMixin, CreateView):
    model = LogFrame
    fields = ['name']
    template_name = 'logframe/create_logframe.html'
    permission_required = 'logframe.edit_logframe'

    def get_unique_slug_name(self, logframe):
        slug = logframe.name.lower()
        slug = slug.replace(' ', '_')
        slug = re.sub('[^\w-]', '', slug)
        slug = slug[:46]
        if LogFrame.objects.filter(slug=slug).exists():
            count = LogFrame.objects.filter(slug__startswith=slug).count() + 1
            slug += unicode(count)
        return slug

    def get_success_url(self):
        return reverse('logframe-dashboard', kwargs={'slug': self.object.slug})

    def form_valid(self, form):
        form.instance.slug = self.get_unique_slug_name(form.instance)
        # The logframe needs to exist before we create the settings, so finish
        # the regular form_valid code.
        response = CreateView.form_valid(self, form)
        Settings.objects.create(logframe=form.instance)
        return response
