import logging
from springframework.web.servlet.view import AbstractUrlBasedView


class InternalResourceView(metaclass=AbstractUrlBasedView):

    alwaysInclude = False
    preventDispatchLoop = False

    def __init__(self, url: str, alwaysInclude: bool) -> None:
        super().__init__(url)
        self.alwaysInclude = alwaysInclude

    def setAlwaysInclude(self, alwaysInclude: bool) -> None:
        self.alwaysInclude = alwaysInclude

    def setPreventDispatchLoop(self, preventDispatchLoop: bool):
        self.preventDispatchLoop = preventDispatchLoop

    def isContextRequired(self) -> bool:
        return False

    def renderMergedOutputModel(self, model: dict, request, response) -> None:
        # Expose the model object as request attributes.
        self.exposeModelAsRequestAttributes(model, request)

        # Expose helpers as request attributes, if any.
        self.exposeHelpers(request)

        # Determine the path for the request dispatcher.
        dispatcherPath: str = self.prepareForRendering(request, response)

        # Obtain a RequestDispatcher for the target resource (typically a JSP).
        # TODO: use mock
        # rd type: RequestDispatcher
        rd = self.getRequestDispatcher(request, dispatcherPath)
        if rd is None:
            raise ValueError(f"""Could not get RequestDispatcher for [{self.getUrl()}
            ]: Check that the corresponding file exists within your web application archive!""")

        # If already included or response already committed, perform include, else forward.
        if self.useInclude(request, response):
            response.setContentType(self.getContentType())
            logging.debug("Including [" + self.getUrl() + "]")
            rd.include(request, response)
        else:
            # Note: The forwarded resource is supposed to determine the content type itself.
            logging.debug("Forwarding to [" + self.getUrl() + "]")
            rd.forward(request, response)

    def exposeHelpers(self, request) -> None:
        pass

    def prepareForRendering(self, request, response) -> str:
        path: str = self.getUrl()
        assert path is not None, "'url' not set"

        if self.preventDispatchLoop:
            uri: str = request.getRequestURI()
            if path.startswith("/"):
                state = (uri == path)
            else:
                # TODO: ignore
                # state = uri.equals(StringUtils.applyRelativePath(uri, path))
                state = False
            if state:
                msg = f"""Circular view path [ {path} ]: would dispatch back
                        to the current handler URL [ {uri} ] again. Check your
                        ViewResolver setup! (Hint: This may be the result of an
                        unspecified view, due to default view name generation.)
                        """
                raise ValueError(msg)
        return path

    # return type: RequestDispatcher
    def getRequestDispatcher(self, request, path: str):
        return request.getRequestDispatcher(path)

    def useInclude(self, request, response):
        # TODO : WebUtils need handle
        # or WebUtils.isIncludeRequest(request)
        return (self.alwaysInclude or response.isCommitted())