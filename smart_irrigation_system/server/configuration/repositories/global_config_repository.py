from sqlmodel import Session, select

from smart_irrigation_system.server.configuration.models.global_config import GlobalConfig


class GlobalConfigRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_singleton(self) -> GlobalConfig | None:
        return self.session.exec(select(GlobalConfig)).first()

    def create(self, config: GlobalConfig) -> GlobalConfig:
        self.session.add(config)
        self.session.flush()
        return config

    def save(self, config: GlobalConfig) -> GlobalConfig:
        self.session.add(config)
        self.session.flush()
        return config
