import logging

from springframework.utils.mock.inst import Locale, Ordered, BeanFactoryUtils, MediaType
from springframework.utils.mock.inst import ContentNegotiationManagerFactoryBean
from springframework.utils.mock.inst import AnnotationAwareOrderComparator
from springframework.utils.mock.inst import RequestContextHolder, ServletWebRequest, RequestAttributes
from springframework.utils.mock.inst import HttpServletResponse
from springframework.beans.factory.InitializingBean import InitializingBean
from springframework.web.context.support.WebApplicationObjectSupport import WebApplicationObjectSupport
from springframework.web.servlet.View import View
from springframework.web.servlet.SmartView import SmartView
from springframework.web.servlet.ViewResolver import ViewResolver


class NotAcceptableView(View):
    def getContentType(self) -> str:
        return None

    def render(self, model: dict, response: HttpServletResponse) -> None:
        response.setStatus(HttpServletResponse.SC_NOT_ACCEPTABLE)


class ContentNegotiatingViewResolver(WebApplicationObjectSupport, ViewResolver, Ordered, InitializingBean):
    cnmFactoryBean = ContentNegotiationManagerFactoryBean()
    useNotAcceptableStatusCode = False
    order = Ordered.HIGHEST_PRECEDENCE

    def setContentNegotiationManager(self, contentNegotiationManager) -> None:
        self.contentNegotiationManager = contentNegotiationManager

    def getContentNegotiationManager(self):
        return self.contentNegotiationManager

    def setUseNotAcceptableStatusCode(self, useNotAcceptableStatusCode: bool) -> None:
        self.useNotAcceptableStatusCode = useNotAcceptableStatusCode

    def isUseNotAcceptableStatusCode(self) -> bool:
        return self.useNotAcceptableStatusCode

    def setDefaultViews(self, defaultViews: list) -> None:
        self.defaultViews = defaultViews

    def getDefaultViews(self) -> list:
        if self.defaultViews is not None:
            return self.defaultViews

        return list()

    def setViewResolvers(self, viewResolvers: list) -> None:
        self.viewResolvers = viewResolvers

    def getViewResolvers(self) -> list:
        if self.viewResolvers is not None:
            return self.viewResolvers

        return list()

    def setOrder(self, order) -> None:
        self.order = order

    def getOrder(self) -> int:
        return self.order

    def initServletContext(self, servletContext: ServletContext) -> None:
        matchingBeans = BeanFactoryUtils.beansOfTypeIncludingAncestors(obtainApplicationContext(), ViewResolver).values()
        if self.viewResolvers is None:
            self.viewResolvers = list()
            for (viewResolver in matchingBeans):
                if self != viewResolver:
                    self.viewResolvers.append(viewResolver)

        else:
            for i in range(len(self.viewResolvers)):
                vr = self.viewResolvers[i]
                if matchingBeans.contains(vr):
                    continue
                name = vr.getClass().getName() + i
                obtainApplicationContext().getAutowireCapableBeanFactory().initializeBean(vr, name)

        AnnotationAwareOrderComparator.sort(self.viewResolvers)
        self.cnmFactoryBean.setServletContext(servletContext)

    def afterPropertiesSet(self) -> None:
        if self.contentNegotiationManager is None:
            self.contentNegotiationManager = self.cnmFactoryBean.build()

        if (self.viewResolvers is None or not self.viewResolvers):
            logging.info("No ViewResolvers configured")

    def resolveViewName(self, viewName: str, locale: Locale) -> View:
        attrs = RequestContextHolder.getRequestAttributes()
        # assert isinstance(attrs, ServletRequestAttributes), "No current ServletRequestAttributes"
        requestMediaTypes = self.getMediaTypes((attrs).getRequest())
        if requestedMediaTypes is not None:
            candidateViews = self.getCandidateViews(viewName, locale, requestedMediaTypes)
            bestView = getBestView(candidateViews, requestedMediaTypes, attrs)
            if bestView is not None:
                return bestView

        if self.useNotAcceptableStatusCode:
            return NOT_ACCEPTABLE_VIEW
        else:
            return None

    def getMediaTypes(self, request) -> list:
        assert self.contentNegotiationManager is not None, "No ContentNegotiationManager set"
        try:
            webRequest = ServletWebRequest(request)
            acceptableMediaTypes = self.contentNegotiationManager.resolveMediaTypes(webRequest)
            producibleMediaTypes = self.getProducibleMediaTypes(request)
            compatibleMediaTypes = list()
            for acceptable in acceptableMediaTypes:
                for producible in producibleMediaTypes:
                    if acceptable.isCompatibleWith(producible):
                        compatibleMediaTypes.append(self.getMostSpecificMediaType(acceptable, producible))
            
            selectedMediaTypes = compatibleMediaTypes
            MediaType.sortBySpecificityAndQuality(selectedMediaTypes)
            return selectedMediaTypes
        except:
            return None

    def getProducibleMediaTypes(self, request) -> list:
        #TODO

    def getCandidateViews(self, viewName: str, locale: Locale, requestMediaTypes: list) -> list:
        candidateViews = list()
        if self.viewResolvers is not None:
            assert self.contentNegotiationManager is not None, "No ContentNegotiationManager set"
            for viewResolver in self.viewResolver:
                view = viewResolver.resolveViewName(viewName, locale)
                if view is not None:
                    candidateViews.append(view)
                for requestedMediaType in requestMediaTypes:
                    extensions = self.contentNegotiationManager.resolveFileExtensions(requestedMediaType)
                    for extension in extensions:
                        viewNameWithExtension = viewName + '.' + extension
                        view = viewResolver.resolveViewName(viewNameWithExtension, locale)
                        if view is not None:
                            candidateViews.add(view)

        if self.defaultViews:
            candidateViews.append(self.defaultViews)

        return candidateViews

    def getBestView(self, candidateViews: list, requestedMediaTypes: list, attrs) -> View:
        for candidateView in candidateViews:
            if isinstance(candidateView, SmartView):
                smartView = candidateView
                if smartView.isRedirectView():
                    return candidateView

        for mediaType in requestedMediaTypes:
            for candidateView in candidateViews:
                if candidateView.getContentType():
                    candidateContentType = MediaType.parseMediaType(candidateView.getContentType())
                    if mediaType.isCompatibleWith(candidateContentType):
                        attrs.setAttribute(View.SELECTED_CONTENT_TYPE, mediaType, RequestAttributes.SCOPE_REQUEST)
                        return candidateView

        return None

    NOT_ACCEPTABLE_VIEW = NotAcceptableView()




