import chevron

from ..services.base import Service


class TemplateService(Service):
  def _escape_args(self, args, escape):
    return {k: escape(v) for k, v in args.items()}

  def _raw_render_template_from_file(self, escape, relative_filename, template_args):
    template = self.services.resource_service.read('template', relative_filename).decode("utf-8")
    return chevron.render(
      template=template,
      data=self._escape_args(template_args, escape),
    )
