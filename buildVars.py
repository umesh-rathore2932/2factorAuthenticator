from site_scons.site_tools.NVDATool.typings import AddonInfo, BrailleTables, SymbolDictionaries, SpeechDictionaries
from site_scons.site_tools.NVDATool.utils import _

addon_info = AddonInfo(
	addon_name="TwoFactorAuthenticator",
	addon_summary=_("2Factor Authenticator"),
	addon_description=_("Generates 2FA TOTP codes quickly via a shortcut key and copies them to the clipboard."),
	addon_version="1.3",
	addon_changelog=_("Initial release with 2FA manager in Tools menu and hotkey NVDA+Ctrl+2."),
	addon_author="Umesh Rathore <umeshrathore897@gmail.com>",
	addon_url="https://github.com/umesh-rathore2932/2factorAuthenticator",	addon_sourceURL="https://github.com/umeshrathore/2factorAuthenticator",
	addon_docFileName="readme.html",
	addon_minimumNVDAVersion="2024.1",
	addon_lastTestedNVDAVersion="2026.1.1",
	addon_updateChannel=None,	addon_license=None,	addon_licenseURL=None,
)

pythonSources: list[str] = [
	"addon/globalPlugins/2factorAuthenticator/__init__.py",
]

i18nSources: list[str] = pythonSources + ["buildVars.py"]
excludedFiles: list[str] = []
baseLanguage: str = "en"
markdownExtensions: list[str] = []
brailleTables: BrailleTables = {}
symbolDictionaries: SymbolDictionaries = {}
speechDictionaries: SpeechDictionaries = {}
