import chevron

from ..services.base import Service


class TemplateService(Service):
  def _dockerfile_escape(self, s):
    return s.replace('\\', '\\\\').replace('\n', '\\\n')

  def render_dockerfile_template_from_file(self, relative_filename, template_args):
    renderer = chevron.render
    return self._raw_render_template_from_file(renderer, relative_filename, template_args)

  def _yaml_escape(self, s):
    return s.replace('\\', '\\\\').replace('"', '\\"')

  def render_yaml_template_from_file(self, relative_filename, template_args):
    renderer = chevron.render
    return self._raw_render_template_from_file(renderer, relative_filename, template_args)

  def _raw_render_template_from_file(self, renderer, relative_filename, template_args):
    template = self.services.resource_service.read('template', relative_filename)
    return renderer.render(template, template_args)
