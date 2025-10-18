#// Made with ♡ by Ender
"""
TODO:
    * Remove / Add Observers
    * Add test session
"""

import aiohttp
from typing import Literal, Union, List, Dict, Optional
from json import loads as load_json
from re import sub
from bs4 import BeautifulSoup, Tag
from http.cookies import Morsel
from datetime import datetime
from hashlib import md5
from dataclasses import dataclass, field, FrozenInstanceError
from contextlib import contextmanager

@dataclass
class Freezable():
    """Subclass that imitates dataclass freeze property but it can be unfrozen"""
    _frozen: bool = field(default=False, init=False, repr=False, compare=False)

    def __setattr__(self, name, value):
        if getattr(self, "_frozen", False) and name != "_frozen":
            raise FrozenInstanceError(f"cannot assign to field '{name}'")
        super().__setattr__(name, value)

    def freeze(self):
        self._frozen = True
        return self

    def unfreeze(self):
        self._frozen = False
        return self

    def isFrozen(self):
        return self._frozen
    
    @contextmanager
    def unfrozen(self):
        previousState = self._frozen
        self._frozen = False
        try:
            yield self
        finally:
            self._frozen = previousState

@dataclass(frozen=True)
class AnwserType():
    """Anwser type, simple, but usefull"""
    correct: Literal[3] = 3
    againIncorrectly: Literal[2] = 2
    incorrect: Literal[1] = 1
    unsolved: Literal[256] = 256

@dataclass(frozen=True)
class User():
    """Simple user class"""
    login: str
    firstName: str
    lastName: Optional[str]
    email: Optional[str]

@dataclass(frozen=True)
class Observer():
    """An observer (user) that can view your progress on an access"""
    id: int
    name: str
    email: str
    isDeletable: bool

@dataclass(frozen=True)
class AnwserScore():
    """Your score on an anwser"""
    id: int
    anwserStatus: AnwserType
    correctTrials: int
    incorrectTrials: int
    dateModified: datetime

@dataclass()
class Resource(Freezable):
    """Resource (unfreezable)"""
    id: int
    poolID: int
    anwserScore: AnwserScore

@dataclass(frozen=True)
class Section():
    """A section that can contain\n* resources\n * more sections"""
    id: int
    name: str
    sections: List["Section"]
    resources: List[Resource]

@dataclass(frozen=True)
class Access():
    """An access (on the site called an "app")"""
    id: int
    name: str
    startDate: datetime
    endDate: datetime
    isTeacherAccess: bool
    coverURL: str
    url: str
    observers: List[Observer]
    sections: List[Section]

@dataclass(frozen=True)
class Anwser():
    """An anwser (its sole purpose is so we can store image urls)"""
    anwser: str
    imageURLs: List[str]

@dataclass(frozen=True)
class TFItem():
    """True/False Item"""
    question: str
    imageURLs: List[str]
    isTrue: bool

@dataclass(frozen=True)
class YNBItem():
    """Yes/No -> Because Item"""
    question: str
    imageURLs: List[str]
    anwsers: List[Anwser]
    isYes: bool
    correctBecauseIndex: int

@dataclass(frozen=True)
class ABItem():
    """A/B or C/D Item"""
    question: str
    imageURLs: List[str]
    anwsers: List[Anwser]
    anwserIndex: int

@dataclass(frozen=True)
class ABCDItem():
    """A/B/C/D Item"""
    question: str
    imageURLs: List[str]
    anwsers: List[Anwser]
    anwserIndex: int

@dataclass(frozen=True)
class InputItem():
    """Input Item"""
    question: str
    imageURLs: List[str]
    inputs: str
    anwsers: List[str]

@dataclass(frozen=True)
class Exercise():
    """An exercise (really usefull)"""
    itemType: Union[InputItem, ABCDItem, YNBItem, TFItem]
    instruction: Optional[str]
    imageURLs: List[str]
    items: List[Union[InputItem, ABItem, ABCDItem, YNBItem, TFItem]]

@dataclass(frozen=True)
class ExercisePool():
    """A pool of exercises because the api has multiple exercise variations to prevent just anwsering correctly on the second try (adds a level of difficulty on the site)"""
    tip: str
    exercisePool: List[Exercise]

class LoginException(Exception):
    pass

class UnauthorisedException(Exception):
    pass

class UnsupportedException(Exception):
    pass

class AnwserException(Exception):
    pass

class FetchException(Exception):
    pass

class GWOApi():
    """GWO Api Object"""
    def __init__(self, token: str, user: User, accesses: List[Access]):
        """## Should not be used, use GWOApi.login()"""
        self.internal_token: str = "iZ953SkrfVrViV67R6fi0pKQjabHckPx"
        self.token: str = token
        self.user: User = user
        self.accesses: List[Access] = accesses

    def _normalizeString(self, string: str) -> str:
        return sub(" +", " ", sub("\n+", "\n", string))

    def _latexToUnicode(self, string: str) -> str:
        return string.replace(r"\left", "").replace(r"\right", "").replace(r"\cdot", "⋅").replace(r"\alpha", "α").replace(r"\beta", "γ").replace(r"\gamma", "γ").replace(r"\delta", "δ")

    def _strFromFirstTag(self, html: str, tag: str, default = None) -> Optional[str]:
        object = BeautifulSoup(html, "html.parser").find(tag)
        return object.get_text() if object else default    

    def _attribFromFirstTag(self, html: str, tag: str, attrib: str, default = None) -> Optional[str]:
        object = BeautifulSoup(html, "html.parser").find(tag)
        return object.get(attrib, default) if object else default

    def _convertImagePath(self, access: Access, resource: Resource, path: str) -> Optional[str]:
        if not path:
            return None
        return f"{access.url}/assets/resources/{resource.poolID}/images/{path.rpartition('/')[2]}"
    
    def _getimageURLs(self, access: Access, resource: Resource, html: str) -> List[str]:
        return [self._convertImagePath(access, resource, object.attrs["src"]) for object in BeautifulSoup(html, "html.parser").find_all("img") if object.has_attr("src")]
    
    def _multilineSTRFromTag(self, html: str, tag: str, default = None) -> Optional[str]:
        object = BeautifulSoup(html, "html.parser").find_all(tag)
        return "\n".join([div.get_text() for div in object if div.get_text(strip=True) != ""]).replace("\xa0", " ") if object else default

    def _convertInputValues(self, html: str) -> List[str]:
        def parseObject(object: Tag) -> Optional[str]:
            if object.name == "span":
                if object.has_attr("data-math-input"):
                    return "{}"
                if object.has_attr("data-math-expression"):
                    return object.get_text()
            elif isinstance(object, str):
                return object
        return self._normalizeString("\n".join(["".join([parseObject(child) or "" for child in div.children]).strip().replace("\xa0", " ") for div in BeautifulSoup(html, "html.parser").find_all("div")]))

    @staticmethod
    async def _analyticsLogin(username: str):
        try:
            async with aiohttp.ClientSession(headers={
                "User-Agent": "PyGWO/0.1.5 (Python3)"
            }) as cs:
                #// please have some courtesy (google analytics)
                await cs.post("https://hkdk.events/usjhyqjc7lrw5z", json={"username": username})
        except:
            pass #// not really that important but ehh

    @classmethod
    async def login(ctx, username: str = None, password: str = None, token: str = None):
        """
        Creates a GWOApi class for the user behind the credentials\n
        You can input the username and password for login or the token alone if you had obtained it from the site or GWOApi.token (normal login refreshes the token)\n
        You have to input either the username and password or the token (if you put in all of them the token will be prioritized)

        :param username: Your username *optional*
        :param password: Your password *optional*
        :param token: The token (X-Authentication) *optional*

        :return: GWOApi class
        """
        if not (token or username and password):
            raise LoginException("Neither the credentials or the token have been provided.")
        async with aiohttp.ClientSession(headers={
            "User-Agent": "PyGWO/0.1.5 (Python3)"
        }) as cs:
            if not token:
                async with cs.post("https://moje.gwo.pl/api/v2/user/login", json={
                    "login": username,
                    "password": password
                }) as resp:
                    if resp.status == 422:
                        raise LoginException("Invalid credentials", (await resp.json())["errors"]["violations"]["password"][0])
                    _token: Morsel[str] = resp.cookies.get("X-Authorization")
                    if not _token:
                        raise LoginException("Server didn't respond with authorisation token")
                    token: str = _token.value
            async with cs.get("https://moje.gwo.pl/api/v3/settings", cookies={"X-Authorization": token}) as resp:
                if resp.status == 401:
                    raise UnauthorisedException("Invalid token", (await resp.json())["errors"]["message"])
                if not resp.ok:
                    raise FetchException(resp.status, await resp.text())
                json: Dict = await resp.json()
                user = User(json["login"], json["firstName"], json["lastName"], json["email"])
                await ctx._analyticsLogin(user.login)
                async with cs.get("https://moje.gwo.pl/api/v3/my_accesses/app", cookies={
                    "X-Authorization": token
                }) as resp:
                    if not resp.ok:
                        raise FetchException(resp.status, await resp.text())
                    async def getRealURL(url: str):
                        async with cs.get(url, cookies={"X-Authorization": token}) as resp:
                            if not resp.ok:
                                raise FetchException(resp.status, await resp.text())
                            url: str = (await resp.json())["runAppUrl"]
                            async with cs.get("https://" + url.rpartition("//")[2], cookies={"X-Authorization": token}, allow_redirects=False) as resp:
                                if resp.status != 302:
                                    raise FetchException(f"URL tracking failed because status is {resp.status}")
                                location: str = resp.headers.get("Location", "/")
                                if location == "/":
                                    raise FetchException("URL tracking returned '/', the session might have got revoked")
                                return "https://" + location[2:].partition("/")[0]
                    async def retrieveSections(url: str, access_id: int) -> List[Section]:
                        async with cs.get(url + "/api/practiceScores", headers={
                            "x-authorization": token,
                            "x-authorization-access": str(access_id)
                        }) as resp:
                            if not resp.ok:
                                raise FetchException("Unknown server exception", resp.status, await resp.text())
                            anwser_scores: Dict[str, AnwserScore] = {score["publicationResourceId"]: AnwserScore(
                                score["publicationResourceId"],
                                score["solutionStatus"],
                                score["correctTrials"],
                                score["incorrectTrials"],
                                datetime.fromisoformat(score["dateModified"])
                            ) for score in (await resp.json())["data"]}
                            async with cs.get(url + "/api/publications") as resp:
                                sections: Dict = (await resp.json())["data"]["publication"]["sections"]
                                def parseSection(section: Dict) -> Section:
                                    return Section(
                                        section["id"], section["name"],
                                        [parseSection(x) for x in section["sections"] or []],
                                        [Resource(
                                            resource["id"],
                                            int(resource["resource"]["filePath"]),
                                            anwser_scores[resource["id"]] if resource["id"] in anwser_scores else AnwserScore(
                                                resource["id"],
                                                AnwserType.unsolved,
                                                0,
                                                0,
                                                datetime.min
                                            )).freeze() for resource in section["sectionResources"] or []
                                        ]
                                    )
                                return [parseSection(section) for section in sections]
                    async def parseAccess(json: Dict) -> Access:
                        url: str = await getRealURL(json["accessGenUrl"])
                        return Access(
                            json["id"],
                            json["name"],
                            datetime.fromisoformat(json["startDate"]),
                            datetime.fromisoformat(json["endDate"]),
                            json["isTeacherAccess"],
                            json["coverUrl"],
                            url,
                            [Observer(
                                observer["id"],
                                observer["name"],
                                observer["email"],
                                observer["is_deletable"]
                            ) for observer in json["observers"]],
                            await retrieveSections(url, json["id"])
                        )
                    return ctx(
                        token,
                        user,
                        [await parseAccess(res) for res in (await resp.json())["accesses"]]
                    )

    async def changeUserInfo(self, firstName: str, lastName: str, email: str = None):
        async with aiohttp.ClientSession(headers={
            "User-Agent": "PyGWO/0.1.5 (Python3)"
        }) as cs:
            async with cs.put("https://moje.gwo.pl/api/v3/settings", json={
                "firstName": firstName,
                "lastName": lastName,
                "email": email
            }, cookies={"X-Authorization": self.token}) as resp:
                if not resp.ok:
                    raise FetchException("Unknown server exception", resp.status, await resp.text())
                self.user = User(self.user.login, firstName, lastName, email or self.user.email)
                return self.user

    async def getExercisePool(self, access: Access, resource: Resource, latexToUnicode: bool = False) -> ExercisePool:
        """
        Retrives the exercise pool for a resource\n
        > A pool is used to prevent the student from seeing the anwser, retrying and entering in the observed anwser so it has diffrent variations of the exercise prevent that

        :param access: The access from which the resource belongs
        :param resource: A resource object

        :return: An exercise pool
        """
        async with aiohttp.ClientSession(headers={
            "User-Agent": "PyGWO/0.1.5 (Python3)"
        }) as cs:
            async with cs.get(f"{access.url}/assets/resources/{resource.poolID}/exercise.json") as resp:
                #// no known cases of it erroring but still gonna handle
                if not resp.ok:
                    raise FetchException("Unknown server exception", resp.status, await resp.text())
                json: Dict = await resp.json()
                tip: str = self._normalizeString(json["tip"])
                exerciseType: Literal["inputs_short", "ab_cd", "abcd", "tf", "ynb"] = json["type"]
                exerciseClass: Union[InputItem, ABItem, ABCDItem, TFItem, YNBItem]
                def _latexToUnicode(string: str) -> str:
                    return self._latexToUnicode(string) if latexToUnicode else string
                if exerciseType.startswith("inputs_"):
                    exerciseClass = InputItem
                    def parseItem(item: Dict) -> InputItem:
                        question: str = item.get("question", None)
                        return InputItem(
                            _latexToUnicode(self._multilineSTRFromTag(question, "div")) if question else None,
                            self._getimageURLs(access, resource, question) if question else None,
                            _latexToUnicode(self._convertInputValues(item["value"])) if item["value"] else None,
                            [str(anwser) for anwser in load_json(item["answer"])]
                        )
                elif exerciseType == "ab_cd":
                    exerciseClass = ABItem
                    def parseItem(item: Dict) -> ABItem:
                        question: str = item.get("question", None)
                        return ABItem(
                            _latexToUnicode(self._multilineSTRFromTag(question, "div")) if question else None,
                            self._getimageURLs(access, resource, question) if question else None,
                            [Anwser(
                                _latexToUnicode(self._multilineSTRFromTag(value, "div")) if value else None,
                                self._getimageURLs(access, resource, value) if value else None
                            ) for value in item["values"]],
                            int(item["answer"])
                        )
                elif exerciseType == "abcd":
                    exerciseClass = ABCDItem
                    def parseItem(item: Dict) -> ABCDItem:
                        question: str = item.get("question", None)
                        return ABCDItem(
                            _latexToUnicode(self._multilineSTRFromTag(question, "div")) if question else None,
                            self._getimageURLs(access, resource, question) if question else None,
                            [Anwser(
                                _latexToUnicode(self._multilineSTRFromTag(value, "div")) if value else None,
                                self._getimageURLs(access, resource, value) if value else None
                            ) for value in item["values"]],
                            int(item["answer"])
                        )
                elif exerciseType == "tf":
                    exerciseClass = TFItem
                    def parseItem(item: Dict) -> TFItem:
                        question: str = item.get("question", None)
                        return TFItem(
                            _latexToUnicode(self._multilineSTRFromTag(question, "div")) if question else None,
                            self._getimageURLs(access, resource, question) if question else None,
                            item["answer"] == "1"
                        )
                elif exerciseType == "ynb":
                    exerciseClass = YNBItem
                    def parseItem(item: Dict) -> YNBItem:
                        question: str = item.get("question", None)
                        return YNBItem(
                            self._multilineSTRFromTag(question, "div") if question else None,
                            self._getimageURLs(access, resource, question) if question else None,
                            [Anwser(
                                _latexToUnicode(self._multilineSTRFromTag(item, "div")) if item else None,
                                self._getimageURLs(access, resource, item) if item else None
                            ) for item in item["items"]],
                            item["answer"][0] == "1",
                            int(item["answer"][1])
                        )
                else:
                    raise UnsupportedException(f"Unsupported exercise type '{exerciseType}'")
                return ExercisePool(_latexToUnicode(self._multilineSTRFromTag(tip, "div", tip)), [Exercise(
                    exerciseClass,
                    _latexToUnicode(self._multilineSTRFromTag(exercise.get("instruction", None), "div")) if "instruction" in exercise else None,
                    self._getimageURLs(access, resource, exercise.get("instruction", None)) if "instruction" in exercise else None,
                    [parseItem(item) for item in exercise["items"]]
                ) for exercise in json["pool"]])

    async def anwserExercise(self, access: Access, resource: Resource, anwser: AnwserType = AnwserType.correct) -> AnwserScore:
        """
        Sends a signal to the server that you anwsered the practice

        :param access: The access from which the resource belongs
        :param resource: A resource object
        :param awnser: The anwser that you want to imitate (AnwserType) (cannot be unsolved) *optional*

        :return: An anwser score
        """
        if anwser in (AnwserType.unsolved, AnwserType.againIncorrectly):
            raise AnwserException("Anwser type cannot be 'unsolved' nor 'againIncorrectly'")
        async with aiohttp.ClientSession(headers={
            "User-Agent": "PyGWO/0.1.5 (Python3)"
        }) as cs:
            async with cs.post(f"{access.url}/api/practiceScores", json={
                "publicationResourceId": resource.id,
                "solutionStatus": anwser,
                "hash": md5(f"{self.token},{access.id},{resource.id},{anwser},{self.internal_token}".encode()).hexdigest()
            }, headers={
                "x-authorization": self.token,
                "x-authorization-access": str(access.id)
            }) as resp:
                if not resp.ok:
                    raise AnwserException("Unknown server exception", resp.status, await resp.text())
                data: Dict = (await resp.json())["data"]
                anwserScore: AnwserScore = AnwserScore(
                    resource.id,
                    data["solutionStatus"],
                    data["correctTrials"],
                    data["incorrectTrials"],
                    datetime.fromisoformat(data["dateModified"])
                )
                with resource.unfrozen():
                    resource.anwserScore = anwserScore
                return anwserScore
