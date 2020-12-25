from mock.inst import Locale
# TODO: import MediaType, ServerWebExchange

class RedirectView(AbstractUrlBasedView):

    # TODO: _URI_TEMPLATE_VARIABLE_PATTERN
    # TODO: _statusCode
    _contextRelative = True
    _propagateQuey = False
    
    def __init__(self, redirectUrl: str = None, statusCode: HttpStatus = None):
        super().__init__(redirectUrl)
        self.set_status_code(statusCode)

    def set_status_code(self, statusCode: HttpStatus) -> None:
        assert statusCode.is3xxRedirection(), "Not a redirect status code"
        self.statusCode = statusCode

    def get_status_code(self) -> HttpStatus:
        return self.statusCode

    def set_context_relative(self, contextRelative: bool) -> None:
        self.contextRelative = contextRelative

    def is_context_relative(self) -> bool:
        return self.contextRelative

    def is_propogate_query(self) -> bool:
        return self.propagateQuery

    def set_hosts(self, hosts: list) -> None:
        self.hosts = hosts
    
    def get_hosts(self) -> list:
        return self.hosts

    def after_properties_set(self) -> None:
        super().after_properties_set()

    def is_redirect_view(self) -> bool:
        return True

    def check_resource_exists(self, locale: Locale) -> bool:
        return True

    def render_internal(self, model: dict, contenType: object, exchange: ServerWebExchange) -> dict:
        return self.send_redirect(targetUrl, exchange)

    def create_target_url(self, model: dict, exchange: ServerWebExchange) -> str:
        url = self.get_url()
        assert url is not None, "'url' not set"

        request = exchange.getRequest()

        # targetUrl = StringBuilder()
        # if (isContextRelative() and url.startsWith("/")):
        #     targetUrl.append()


    def get_current_uri_variables(self, exchange: ServerWebExchange) -> dict:
        # TODO: HandlerMapping
        pass
        # name = HandlerMapping.URI_TEMPLATE_VARIABLES_ATTRIBUTE
        # return exchange.getattr(name, Collections.emptyMap())

    # def expandTargetUrlTemplate()

    def encode_uri_variable(self, text: str) -> str:
        # TODO: UriUtils
        pass
        # return UriUtils.encode(text, StandardCharsts.UTF_8)

    # def appendCurrentRequestQuery()

    # def sendRedirect()

    def is_remote_host(self, targetUrl: str) -> bool:
        if self.hosts is not None:
            return False
        # TODO: UricomponentsBuilder
        # targetHost = UriComponentsBuilder.fromUriString(targetUrl).build().getHost()
        # if not StringUtils.hasLength(targetHost):
        #     return False

        for host in self.hosts:
            if targetHost == host:
                return False

        return True


    

    

