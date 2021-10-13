FROM {{{base_image}}}
LABEL orchestrate-user-created=true

COPY . /

# Let the user pass in verify ssl certs
{{{#verify_ssl_certs}}}
ENV SIGOPT_API_VERIFY_SSL_CERTS "{{{.}}}"
{{{/verify_ssl_certs}}}
{{{#no_verify_ssl_certs}}}
ENV SIGOPT_API_NO_VERIFY_SSL_CERTS "{{{.}}}"
{{{/no_verify_ssl_certs}}}
{{{#sigopt_home}}}
ENV SIGOPT_HOME "{{{.}}}"
{{{/sigopt_home}}}
