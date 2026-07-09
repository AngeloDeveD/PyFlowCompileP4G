from __future__ import annotations

from dataclasses import dataclass, replace
from enum import IntEnum

from .ids import Bustup


@dataclass(frozen=True)
class FlowEnumValue:
    """Named FlowScript enum value rendered as EnumName.MemberName.

    P4G decompiled scripts use enum-like names such as SocialStat.Courage. These
    values should render exactly that text instead of becoming Python integers.
    """

    enum_name: str
    member_name: str

    def render_flow(self) -> str:
        """Render this value exactly as FlowScript expects it."""
        return f"{self.enum_name}.{self.member_name}"

    def __str__(self) -> str:
        """Return the FlowScript representation for string formatting."""
        return self.render_flow()


@dataclass(frozen=True)
class SpeakerName:
    """Display name used in a generated MessageScript speaker tag."""

    display_name: str

    def __str__(self) -> str:
        """Return the exact text written into [msg NAME [Speaker]]."""
        return self.display_name


class Speaker:
    """Common P4G speaker names for proc.say(...) and project.message(...).

    These constants prevent beginners from repeatedly typing speaker strings and
    accidentally creating inconsistent names. Both uppercase constants and
    title-case aliases are provided so code can stay readable in examples.
    """

    MAIN_CHARACTER = SpeakerName("Var 0")
    NANAKO = SpeakerName("Nanako")
    DOJIMA = SpeakerName("Dojima")
    YOSUKE = SpeakerName("Yosuke")
    CHIE = SpeakerName("Chie")
    TEDDIE = SpeakerName("Teddie")
    YUKIKO = SpeakerName("Yukiko")
    KANJI = SpeakerName("Kanji")
    RISE = SpeakerName("Rise")
    NAOTO = SpeakerName("Naoto")
    MARIE = SpeakerName("Marie")
    ADACHI = SpeakerName("Adachi")
    MARGARET = SpeakerName("Margaret")
    IGOR = SpeakerName("Igor")
    AI = SpeakerName("Ai")
    AIKA = SpeakerName("Aika")
    AYANE = SpeakerName("Ayane")
    DAISUKE = SpeakerName("Daisuke")
    ERI = SpeakerName("Eri")
    FOX = SpeakerName("Fox")
    HANAKO = SpeakerName("Hanako")
    HISANO = SpeakerName("Hisano")
    MOROOKA = SpeakerName("Morooka")
    KOU = SpeakerName("Kou")
    MAYUMI = SpeakerName("Mayumi")
    MISUZU = SpeakerName("Misuzu")
    MITSUO = SpeakerName("Mitsuo")
    GAS_STATION = SpeakerName("GasStation")
    EDOGAWA = SpeakerName("Edogawa")
    NAOKI = SpeakerName("Naoki")
    KASHIWAGI = SpeakerName("Kashiwagi")
    SHIROKU = SpeakerName("Shiroku")
    TANAKA = SpeakerName("Tanaka")
    SAKI = SpeakerName("Saki")
    SAYOKO = SpeakerName("Sayoko")
    SHU = SpeakerName("Shu")
    NAMATAME = SpeakerName("Namatame")
    YUMI = SpeakerName("Yumi")
    YUUTA = SpeakerName("Yuuta")

    MainCharacter = MAIN_CHARACTER
    Nanako = NANAKO
    Dojima = DOJIMA
    Yosuke = YOSUKE
    Chie = CHIE
    Teddie = TEDDIE
    Yukiko = YUKIKO
    Kanji = KANJI
    Rise = RISE
    Naoto = NAOTO
    Marie = MARIE
    Adachi = ADACHI
    Margaret = MARGARET
    Igor = IGOR
    Ai = AI
    Aika = AIKA
    Ayane = AYANE
    Daisuke = DAISUKE
    Eri = ERI
    Fox = FOX
    Hanako = HANAKO
    Hisano = HISANO
    Morooka = MOROOKA
    Kou = KOU
    Mayumi = MAYUMI
    Misuzu = MISUZU
    Mitsuo = MITSUO
    GasStation = GAS_STATION
    Edogawa = EDOGAWA
    Naoki = NAOKI
    Kashiwagi = KASHIWAGI
    Shiroku = SHIROKU
    Tanaka = TANAKA
    Saki = SAKI
    Sayoko = SAYOKO
    Shu = SHU
    Namatame = NAMATAME
    Yumi = YUMI
    Yuuta = YUUTA


@dataclass(frozen=True)
class CharacterProfile:
    """Known P4G character with a readable name and default portrait.

    Use Character.YOSUKE when a message should display both the speaker name and
    the standard bustup portrait without remembering raw [bup ...] numbers. Use
    with_name(...) when a translation patch needs a custom visible speaker name
    but should keep the same portrait data.
    """

    display_name: str
    character_id: int | None = None
    default_expression_id: int = 1
    default_costume_id: int = 65535
    default_position: int = 1

    def __str__(self) -> str:
        """Return the exact speaker text written into [msg NAME [Speaker]]."""
        return self.display_name

    def with_name(self, display_name: str) -> "CharacterProfile":
        """Return the same character portrait with a different speaker name.

        This is useful for fan translations where the visible name must be
        encoded differently from the English default, while the bustup id stays
        the same.
        """
        return replace(self, display_name=display_name)

    def portrait(
        self,
        expression_id: int | None = None,
        *,
        costume_id: int | None = None,
        position: int | None = None,
    ) -> Bustup:
        """Return this character's bustup portrait for a message line.

        expression_id changes the facial expression. costume_id and position
        default to the normal P4G dialogue values used by decompiled scripts.
        """
        if self.character_id is None:
            raise ValueError(f"Character has no known bustup id: {self.display_name}")
        return Bustup(
            character_id=self.character_id,
            expression_id=self.default_expression_id if expression_id is None else expression_id,
            costume_id=self.default_costume_id if costume_id is None else costume_id,
            position=self.default_position if position is None else position,
        )

    @property
    def default_bustup(self) -> Bustup | None:
        """Return the default bustup used when this character speaks."""
        if self.character_id is None:
            return None
        return self.portrait()

    @property
    def normal(self) -> Bustup:
        """Return the character's normal dialogue portrait."""
        return self.portrait()


class Character:
    """Common P4G characters with built-in speaker names and portraits.

    The raw Bustup class remains available for advanced cases. These constants
    are intended for beginner-friendly dialogue code where the user should write
    the character's name instead of memorizing portrait ids.
    """

    YOSUKE = CharacterProfile("Yosuke", character_id=2)

    Yosuke = YOSUKE


class SocialStat:
    """P4G social stat enum values used by GET_SOCIAL_STAT_LEVEL.

    These render as FlowScript enum values such as SocialStat.Courage. Use them
    with socialStatLevel(...), for example socialStatLevel(SocialStat.COURAGE) >= 3.
    """

    COURAGE = FlowEnumValue("SocialStat", "Courage")
    KNOWLEDGE = FlowEnumValue("SocialStat", "Knowledge")
    DILIGENCE = FlowEnumValue("SocialStat", "Diligence")
    UNDERSTANDING = FlowEnumValue("SocialStat", "Understanding")
    EXPRESSION = FlowEnumValue("SocialStat", "Expression")

    Courage = COURAGE
    Knowledge = KNOWLEDGE
    Diligence = DILIGENCE
    Understanding = UNDERSTANDING
    Expression = EXPRESSION


class TimeOfDay(IntEnum):
    """Known P4G values returned by GET_TIME_OF_DAY().

    These values describe the current day slot, not a date range. Use
    timeOfDay() == TimeOfDay.EVENING for evening checks. Use checkTimeSpan(...)
    for calendar ranges such as April 1 through May 6.
    """

    LATE_NIGHT = 0
    UNKNOWN_1 = 1
    UNKNOWN_2 = 2
    SCHOOL = 3
    DAY = 4
    EVENING = 5

