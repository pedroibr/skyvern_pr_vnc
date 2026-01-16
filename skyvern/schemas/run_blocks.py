from enum import StrEnum
import re
from urllib.parse import urlparse

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from skyvern.config import settings
from skyvern.schemas.docs.doc_strings import OP_API_KEY_DOC_STRING, OP_MODEL_DOC_STRING, PROXY_URL_DOC_STRING
from skyvern.schemas.runs import ProxyLocation


class CredentialType(StrEnum):
    skyvern = "skyvern"
    bitwarden = "bitwarden"
    onepassword = "1password"
    azure_vault = "azure_vault"


class BaseRunBlockRequest(BaseModel):
    """Base class for run block requests with common browser automation parameters"""

    url: str | None = Field(default=None, description="Website URL")
    webhook_url: str | None = Field(default=None, description="Webhook URL to send status updates")
    proxy_location: ProxyLocation | None = Field(default=None, description="Proxy location to use")
    proxy_url: str | None = Field(
        default=None,
        description=PROXY_URL_DOC_STRING,
        examples=["http://user:pass@host:port", "socks5://user:pass@host:port"],
    )
    op_model: str | None = Field(
        default=None,
        description=OP_MODEL_DOC_STRING,
        examples=["openai/gpt-4o-mini", "mistralai/mistral-small-3.1-24b-instruct"],
    )
    op_api_key: str | None = Field(
        default=None,
        description=OP_API_KEY_DOC_STRING,
        examples=["sk-or-1234567890"],
    )
    totp_identifier: str | None = Field(
        default=None, description="Identifier for TOTP (Time-based One-Time Password) if required"
    )
    totp_url: str | None = Field(default=None, description="TOTP URL to fetch one-time passwords")
    browser_session_id: str | None = Field(
        default=None,
        description="ID of the browser session to use, which is prefixed by `pbs_` e.g. `pbs_123456`",
        examples=["pbs_123456"],
    )
    browser_profile_id: str | None = Field(
        default=None,
        description="ID of a browser profile to reuse for this run",
    )
    browser_address: str | None = Field(
        default=None,
        description="The CDP address for the task.",
        examples=["http://127.0.0.1:9222", "ws://127.0.0.1:9222/devtools/browser/1234567890"],
    )
    extra_http_headers: dict[str, str] | None = Field(
        default=None, description="Additional HTTP headers to include in requests"
    )
    max_screenshot_scrolling_times: int | None = Field(
        default=None, description="Maximum number of times to scroll for screenshots"
    )

    @field_validator("proxy_url")
    @classmethod
    def validate_proxy_url(cls, proxy_url: str | None) -> str | None:
        if not proxy_url:
            return proxy_url
        if not _is_valid_proxy_url(proxy_url):
            raise ValueError("proxy_url must be a valid proxy URL (http/https/socks5)")
        return proxy_url

    @field_validator("op_api_key")
    @classmethod
    def validate_op_keys(cls, op_api_key: str | None, info: ValidationInfo) -> str | None:
        op_model = info.data.get("op_model") if info.data else None
        if op_api_key and not op_model and not settings.OPENROUTER_MODEL:
            raise ValueError("op_model is required when no default OpenRouter model is configured")
        return op_api_key

    @field_validator("op_model")
    @classmethod
    def normalize_op_model(cls, op_model: str | None, info: ValidationInfo) -> str | None:
        if not op_model:
            return op_model
        op_api_key = info.data.get("op_api_key") if info.data else None
        if not op_api_key and not settings.OPENROUTER_API_KEY:
            raise ValueError("op_api_key is required when no default OpenRouter API key is configured")
        if op_model.startswith("openrouter/"):
            return op_model.split("openrouter/", 1)[1]
        return op_model


def _is_valid_proxy_url(url: str) -> bool:
    proxy_pattern = re.compile(r"^(http|https|socks5):\/\/([^:@]+(:[^@]*)?@)?[^\s:\/]+(:\d+)?$")
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        return bool(proxy_pattern.match(url))
    except Exception:
        return False


class LoginRequest(BaseRunBlockRequest):
    credential_type: CredentialType = Field(..., description="Where to get the credential from")
    prompt: str | None = Field(
        default=None,
        description="Login instructions. Skyvern has default prompt/instruction for login if this field is not provided.",
    )

    # Skyvern credential
    credential_id: str | None = Field(
        default=None, description="ID of the Skyvern credential to use for login.", examples=["cred_123"]
    )

    # Bitwarden credential
    bitwarden_collection_id: str | None = Field(
        default=None,
        description="Bitwarden collection ID. You can find it in the Bitwarden collection URL. e.g. `https://vault.bitwarden.com/vaults/collection_id/items`",
    )
    bitwarden_item_id: str | None = Field(default=None, description="Bitwarden item ID")

    # 1Password credential
    onepassword_vault_id: str | None = Field(default=None, description="1Password vault ID")
    onepassword_item_id: str | None = Field(default=None, description="1Password item ID")

    # Azure Vault credential
    azure_vault_name: str | None = Field(default=None, description="Azure Vault Name")
    azure_vault_username_key: str | None = Field(default=None, description="Azure Vault username key")
    azure_vault_password_key: str | None = Field(default=None, description="Azure Vault password key")
    azure_vault_totp_secret_key: str | None = Field(default=None, description="Azure Vault TOTP secret key")


class DownloadFilesRequest(BaseRunBlockRequest):
    navigation_goal: str = Field(..., description="Instructions for navigating to and downloading the file")
    download_suffix: str | None = Field(default=None, description="Suffix or complete filename for the downloaded file")
    download_timeout: float | None = Field(default=None, description="Timeout in seconds for the download operation")
    max_steps_per_run: int | None = Field(default=None, description="Maximum number of steps to execute")
