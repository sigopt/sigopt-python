import chevron

from ..services.base import Service


class TemplateService(Service):
  def _dockerfile_escape(self, s):
    return s.replace('\\', '\\\\').replace('\n', '\\\n')

  def render_dockerfile_template_from_file(self, relative_filename, template_args):
    return self._raw_render_template_from_file(self._dockerfile_escape, relative_filename, template_args)

  def _yaml_escape(self, s):
    return s.replace('\\', '\\\\').replace('"', '\\"')

  def render_yaml_template_from_file(self, relative_filename, template_args):
    return self._raw_render_template_from_file(self._yaml_escape, relative_filename, template_args)

  def _raw_render_template_from_file(self, escape, relative_filename, template_args):
    template = self.services.resource_service.read('template', relative_filename).decode("utf-8")
    return chevron.render(
      template=template,
      data=template_args,
      escape=escape,
    )
