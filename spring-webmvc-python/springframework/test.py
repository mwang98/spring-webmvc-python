from springframework.web.servlet.DispatcherServlet import DispatcherServlet
from springframework.web.testfixture.servlet.MockServletConfig import MockServletConfig
from springframework.web.testfixture.servlet.MockServletContext import MockServletContext


def main():
    servletConfig = MockServletConfig(MockServletContext, servletName='simple')
    dispatcherServelet = DispatcherServlet()

    dispatcherServelet.set


if __name__ == 'main':
    main()
