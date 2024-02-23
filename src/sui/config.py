import pydantic_settings
import toml

class

class Config(pydantic_settings.BaseSettings):
    base_url: str


file_settings = toml.load("config.toml")
settings = Config.model_validate(file_settings["sui"]["reports"])


if __name__ == "__main__":
    print(settings)
    # print(settings.model_config)
