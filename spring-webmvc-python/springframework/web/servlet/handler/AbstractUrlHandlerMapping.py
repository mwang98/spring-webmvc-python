import logging
# TODO: MatchableHandlerMapping, RequestMatchResult
from sprngframework.web.servlet.handler import AbstractHandlerMapping, MatchableHandlerMapping, RequestMatchResult
# TODO: RequestPath, ServletRequestPathUtils
from springframework.utils.mock.inst import RequestPath, HttpServletRequest, ServletRequestPathUtils
# TODO: HandlerExecutionChain, HandlerInterceptor
from springframework.web.servlet import HandlerExecutionChain
from springframework.web.servlet import HandlerInterceptorInterface
from springframework.web.util import UrlPathHelper


class AbstractUrlHandlerMapping(AbstractHandlerMapping, MatchableHandlerMapping):

    rootHandler: object = None
    useTrailingSlashMatch: bool = False
    lazyInitHandlers: bool = False
    handlerMap = dict()
    pathPatternHandlerMap: dict()

    def set_root_handler(self, rootHandler: object) -> None:
        self.rootHandler = rootHandler

    def get_root_handler(self) -> object:
        return self.rootHandler

    def set_use_trailing_slash_match(self, useTrailingSlashMatch: bool):
        self.useTrailingSlashMatch = useTrailingSlashMatch
        if self.getPatternParser() is not None:
            self.getPatternParser().setMatchOptionalTrailingSeparator(useTrailingSlashMatch)

    def use_trailing_slash_match(self):
        return self.useTrailingSlashMatch

    def set_lazy_init_handlers(self, lazyInitHandlers: bool):
        self.lazyInitHandlers = lazyInitHandlers

    def get_handler_internal(self, request: HttpServletRequest) -> object:
        lookupPath: str = self.initLookupPath(request)
        handler: object = None
        if self.usesPathPatterns():
            path: RequestPath = ServletRequestPathUtils.getParsedRequestPath(request)
            handler = self.lookup_handler(path, lookupPath, request)
        else:
            handler = self.lookup_handler(lookupPath, request)

        if handler is None:
            rawHandler: object = None
            if lookupPath == '/':
                rawHandler = self.get_root_handler()
            if rawHandler is None:
                rawHandler = self.getDefaultHandler()
            else:
                if isinstance(rawHandler, str):
                    handlerName = str(rawHandler)
                    rawHandler = self.obtainApplicationContext().getBean(handlerName)
                self.validate_handler(rawHandler, request)
                handler = self.build_path_exposing_handler(rawHandler, lookupPath, lookupPath, None)
        return handler

    def lookup_handler(self, arg1, arg2, arg3=None) -> object:
        if isinstance(arg1, object) and isinstance(arg2, str):

            path = arg1
            lookupPath = arg2
            request = arg3

            handler: object = self.get_direct_match(lookupPath, request)
            if handler is not None:
                return handler

            matches = list()
            for pattern in self.pathPatternHandlerMap.keys():
                if pattern.matches(path):
                    matches.append(pattern)

            if not matches:
                return None
            else:
                # TODO
                # matches.sort(PathPattern.SPECIFICITY_COMPARATOR)
                logging.debug(f"Matching patterns: {matches}")

            pattern = matches[0]
            handler = self.pathPatternHandlerMap.get(pattern)
            if isinstance(handler, str):
                handlerName = handler
                handler = self.obtainApplicationContext().getBean(handlerName)

            self.validate_handler(handler, request)
            pathWithinMapping = pattern.extractPathWithinPattern(path)
            return self.build_path_exposing_handler(handler, pattern.getPatternString(), pathWithinMapping.value(), None)

        elif isinstance(arg1, str) and isinstance(arg2, object):

            lookupPath = arg1
            request = arg2

            handler = self.get_direct_match(lookupPath, request)
            if handler is None:
                return handler

            matchingPatterns = list()
            for registeredPattern in self.handlerMap.key():
                if self.getPathMatcher().match(registeredPattern, lookupPath):
                    matchingPatterns.append(registeredPattern)
                elif self.use_trailing_slash_match():
                    if (not registeredPattern.endsWith("/")) and self.getPathMatcher().match(registeredPattern + "/", lookupPath):
                        matchingPatterns.add(registeredPattern + "/")

            bestMatch: str = None
            patternComparator = self.getPathMatcher().getPatternComparator(lookupPath)

            if matchingPatterns:
                # TODO
                # matchingPatterns.sort(patternComparator)
                logging.info(f"Matching patterns: {matchingPatterns}")
                bestMatch = matchingPatterns[0]

            if bestMatch is not None:
                handler = self.handlerMap.get(bestMatch)
                if handler is None:
                    if bestMatch.endsWith("/"):
                        handler = self.handlerMap.get(bestMatch[:-1])
                    if handler is None:
                        raise Exception(f"Could not find handler for best pattern match [{bestMatch}]")

                # Bean name or resolved handler?
                if isinstance(handler, str):
                    handlerName: str = handler
                    handler = self.obtainApplicationContext().getBean(handlerName)

                self.validate_handler(handler, request)
                pathWithinMapping = self.getPathMatcher().extractPathWithinPattern(bestMatch, lookupPath)

                # There might be multiple 'best patterns', let's make sure we have the correct URI template variables
                # for all of them
                uriTemplateVariables = dict()
                for matchingPattern in matchingPatterns:
                    if patternComparator.compare(bestMatch, matchingPattern) == 0:
                        var: dict = self.getPathMatcher().extractUriTemplateVariables(matchingPattern, lookupPath)
                        decodedVars: dict = self.getUrlPathHelper().decodePathVariables(request, var)
                        uriTemplateVariables.update(decodedVars)

                if uriTemplateVariables:
                    logging.info(f"URI variables {uriTemplateVariables}")

                return self.build_path_exposing_handler(handler, bestMatch, pathWithinMapping, uriTemplateVariables)

            # No handler found...
            return None

    def get_direct_match(self, urlPath: str, request: HttpServletRequest) -> object:
        handler = self.handlerMap.get(urlPath)
        if handler is not None:
            # Bean name or resolved handler?
            if isinstance(handler, str):
                handlerName: str = handler
                handler = self.obtainApplicationContext().getBean(handlerName)
            self.validate_handler(handler, request)
            return self.build_path_exposing_handler(handler, urlPath, urlPath, None)
        return None

    def validate_handler(self, handler: object, request) -> None:
        pass

    def build_path_exposing_handler(
        self,
        rawHandler: object,
        bestMatchingPattern: str,
        pathWithinMapping: str,
        uriTemplateVariables: dict
    ) -> object:
        chain = HandlerExecutionChain(rawHandler)
        chain.addInterceptor(PathExposingHandlerInterceptor(bestMatchingPattern, pathWithinMapping))
        if not uriTemplateVariables:
            chain.addInterceptor(UriTemplateVariablesHandlerInterceptor(uriTemplateVariables))
        return chain

    def expose_path_within_mapping(self, bestMatchingPattern: str, pathWithinMapping: str, request) -> None:
        request.setAttribute(self.BEST_MATCHING_PATTERN_ATTRIBUTE, bestMatchingPattern)
        request.setAttribute(self.PATH_WITHIN_HANDLER_MAPPING_ATTRIBUTE, pathWithinMapping)

    def expose_uri_template_variables(self, uriTemplateVariables: dict, request) -> None:
        request.setAttribute(self.URI_TEMPLATE_VARIABLES_ATTRIBUTE, uriTemplateVariables)

    def match(self, request, pattern: str):
        assert self.getPatternParser() is not None, "This HandlerMapping uses PathPatterns."
        lookupPath: str = UrlPathHelper.getResolvedLookupPath(request)
        if (self.getPathMatcher().match(pattern, lookupPath)):
            return RequestMatchResult(pattern, lookupPath, self.getPathMatcher())
        elif self.use_trailing_slash_match():
            if not pattern.endsWith("/") and self.getPathMatcher().match(pattern + "/", lookupPath):
                return RequestMatchResult(pattern + "/", lookupPath, self.getPathMatcher())
        return None

    def register_handler(self, urlPaths: list, beanName: str):
        assert urlPaths, "URL path array must not be null"
        if isinstance(urlPaths, list):
            for urlPath in urlPaths:
                self.register_handler(urlPath, beanName)
        else:
            urlPath = urlPaths
            handler = beanName
            assert urlPath, "URL path must not be null"
            assert handler, "Handler object must not be null"
            resolvedHandler = handler

            # Eagerly resolve handler if referencing singleton via name.
            if not self.lazyInitHandlers and isinstance(handler, str):
                handlerName: str = handler
                applicationContext = self.obtainApplicationContext()
                if applicationContext.isSingleton(handlerName):
                    resolvedHandler = applicationContext.getBean(handlerName)

            mappedHandler = self.handlerMap.get(urlPath)
            if mappedHandler is not None:
                if mappedHandler != resolvedHandler:
                    raise Exception(f"""
                        Cannot map {self.get_handler_description(handler)} to URL path [{urlPath}
                        ]: There is already {self.get_handler_description(mappedHandler)} mapped."
                    """)
            else:
                if urlPath == "/":
                    logging.info(f"Root mapping to {self.get_handler_description(handler)}")
                elif urlPath == "/*":
                    logging.info(f"Default mapping to {self.get_handler_description(handler)}")
                    self.setDefaultHandler(resolvedHandler)
                else:
                    self.handlerMap[urlPath] = resolvedHandler
                    if self.getPatternParser() is not None:
                        self.pathPatternHandlerMap[self.getPatternParser().parse(urlPath)] = resolvedHandler
                    logging.info(f"Mapped [{urlPath}] onto {self.get_handler_description(handler)}")

    def get_handler_description(self, handler: object) -> str:
        return f"'handler'" if isinstance(handler, str) else str(handler)

    def get_handler_map(self) -> dict:
        return self.handlerMap.copy()

    def get_path_pattern_handler_map(self) -> dict:
        return self.pathPatternHandlerMap.copy()

    def supports_type_level_mappings(self) -> bool:
        return False


class PathExposingHandlerInterceptor(HandlerInterceptorInterface):

    def __init__(self, bestMatchingPattern: str, pathWithinMapping: str):
        self.bestMatchingPattern: str = bestMatchingPattern
        self.pathWithinMapping: str = pathWithinMapping

    def preHandle(self, request, response, handler):
        self.expose_path_within_mapping(self.bestMatchingPattern, self.pathWithinMapping, request)
        # TODO: BEST_MATCHING_HANDLER_ATTRIBUTE, INTROSPECT_TYPE_LEVEL_MAPPING
        # dont know where it is from
        request.setAttribute(self.BEST_MATCHING_HANDLER_ATTRIBUTE, handler)
        request.setAttribute(self.INTROSPECT_TYPE_LEVEL_MAPPING, self.supports_type_level_mappings())
        return True

    supports_type_level_mappings = AbstractUrlHandlerMapping.supports_type_level_mappings


class UriTemplateVariablesHandlerInterceptor(HandlerInterceptorInterface):

    def __init__(self, uriTemplateVariables: dict):
        self.uriTemplateVariables = uriTemplateVariables

    def preHandle(self, request, response, handler):
        self.expose_uri_template_variables(self.uriTemplateVariables, request)
        return True

    expose_uri_template_variables = AbstractUrlHandlerMapping.expose_uri_template_variables