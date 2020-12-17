from abc import ABC, ABCMeta, abstractmethod


class ApplicationContext(metaclass=EnvironmentCapable, ListableBeanFactory, HierarchicalBeanFactory,
                         MessageSource, ApplicationEventPublisher, ResourcePatternResolver):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def get_id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_application_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_display_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_startup_date(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_parent(self) -> object:
        raise NotImplementedError

    @abstractmethod
    def get_autowire_capable_bean_factory(self) -> object:
        raise NotImplementedError