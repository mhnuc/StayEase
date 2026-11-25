import copy
from django.template import context

def _patched_base_context_copy(self):
    duplicate = self.__class__.__new__(self.__class__)
    duplicate.dicts = self.dicts[:]
    return duplicate

def _patched_context_copy(self):
    duplicate = self.__class__.__new__(self.__class__)
    duplicate.dicts = self.dicts[:]
    duplicate.render_context = copy.copy(self.render_context)
    duplicate.autoescape = self.autoescape
    duplicate.use_l10n = self.use_l10n
    duplicate.use_tz = self.use_tz
    duplicate.template_name = self.template_name
    duplicate.template = self.template
    return duplicate

context.BaseContext.__copy__ = _patched_base_context_copy
context.Context.__copy__ = _patched_context_copy
