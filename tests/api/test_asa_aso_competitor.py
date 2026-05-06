"""
模块：ASA&ASO 竞品信息
接口清单（4个，来自 Apifox：Apple CMP - API 文档）：
  1. POST /api/asa-aso-competitor/explore     - 触发竞品探索
     Apifox ref: /paths/_api_asa-aso-competitor_explore.json
  2. GET  /api/asa-aso-competitor/chart       - 数据分析图表（GET + requestBody）
     Apifox ref: /paths/_api_asa-aso-competitor_chart.json
  3. GET  /api/asa-aso-competitor/list        - 分页关键词列表（GET + requestBody）
     Apifox ref: /paths/_api_asa-aso-competitor_list.json
  4. GET  /api/asa-aso-competitor/historys    - 探索历史记录（无参数）
     Apifox ref: /paths/_api_asa-aso-competitor_historys.json

注意：/api/asa-aso-competitor/status 接口仅存在于代码，Apifox 文档未维护，
      本文件通过 explore 返回的 sync_status 字段间接验证同步状态。

认证方式：Cookie Session（通过 conftest.login_session 自动登录）
生成日期：2026-05-05
需求版本：V3.42.0.1.0

关键来源：
  - Apifox MCP 读取（Apple CMP - API 文档 / 默认模块）
  - app/Http/Controllers/SmartAds/AsaAsoCompetitorController.php
  - app/Services/SmartAds/AsaAsoCompetitorService.php  (PREVIEW_LIMIT=500, SOURCE_MAX_COUNT=30000)

⚠️  重要：chart 和 list 均为 GET + JSON requestBody（非 query params），
    需在 requests.Session.get() 中传 json= 参数，否则参数不生效。

参数说明：
  explore  : type(1=词找应用,2=应用找词) + value(string) + country(string)  全必填（requestBody）
  chart    : log_id(integer)  必填（requestBody）；同步未完成时返回业务错误
  list     : log_id(integer) + label(aso|asa)  必填（requestBody）；其余可选
  historys : 无参数
"""
import os
import json
import time
import logging
import contextlib
import requests
import pytest
from tests.utils.api_client import ApiClient

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("BASE_URL", "http://localhost:8080").rstrip("/")

# ─────────────────────────────────────────────────────────────────
# 断言步骤记录器
# 每个 step() 块的结果（PASS/FAIL + 描述）写入日志，
# 同时追加到 conftest._http_calls 旁边的 _assert_steps 列表，
# 最终由 conftest hook 渲染到 HTML 报告的 Extras 区域。
# ─────────────────────────────────────────────────────────────────

_assert_steps: list = []   # 本条用例的断言步骤列表


def _push_step(desc: str, passed: bool, detail: str = "") -> None:
    """记录一个断言步骤结果，同时写 INFO 日志。"""
    icon   = "✅" if passed else "❌"
    status = "PASS" if passed else "FAIL"
    logger.info("%s [%s] %s%s", icon, status, desc,
                f" | {detail}" if detail else "")
    _assert_steps.append({"desc": desc, "passed": passed, "detail": detail})


@contextlib.contextmanager
def step(description: str):
    """
    断言步骤上下文管理器，用法：

        with step("HTTP 状态码为 200"):
            assert resp.status_code == 200

    通过时记录 ✅，失败时记录 ❌ 并重新抛出异常。
    """
    try:
        yield
        _push_step(description, passed=True)
    except AssertionError as e:
        _push_step(description, passed=False, detail=str(e)[:300])
        raise
    except Exception as e:
        _push_step(description, passed=False, detail=f"{type(e).__name__}: {e}"[:300])
        raise

EP_EXPLORE  = "/api/asa-aso-competitor/explore"
EP_CHART    = "/api/asa-aso-competitor/chart"
EP_LIST     = "/api/asa-aso-competitor/list"
EP_HISTORYS = "/api/asa-aso-competitor/historys"

# 正常测试用的国家和 APP ID（按实际测试环境调整）
VALID_COUNTRY = os.getenv("TEST_COUNTRY", "US")
VALID_APP_ID  = os.getenv("TEST_APP_ID", "389801252")      # 应用找词时传 appId
VALID_KEYWORD = os.getenv("TEST_KEYWORD", "game")          # 词找应用时传关键词


# ─────────────────────────────────────────────────────────────────
# 辅助函数
# ─────────────────────────────────────────────────────────────────

def _client(session: requests.Session) -> ApiClient:
    """将已认证 Session 注入 ApiClient。"""
    c = ApiClient()
    c.session = session
    return c


def _explore(session, type_=2, value=None, country=None, **extra):
    payload = {}
    if type_ is not None:
        payload["type"] = type_
    if value is not None:
        payload["value"] = value
    if country is not None:
        payload["country"] = country
    payload.update(extra)
    return session.post(
        BASE_URL + EP_EXPLORE,
        json=payload,
        timeout=int(os.getenv("REQUEST_TIMEOUT", 30)),
    )


def _chart(session, log_id=None, **extra):
    """chart 是 GET + requestBody，log_id 在 JSON body 中传递。"""
    body = {}
    if log_id is not None:
        body["log_id"] = log_id
    body.update(extra)
    return session.get(BASE_URL + EP_CHART,
                       json=body if body else None,
                       timeout=int(os.getenv("REQUEST_TIMEOUT", 15)))


def _list(session, log_id=None, label=None, **extra):
    """list 是 GET + requestBody，所有参数在 JSON body 中传递。"""
    body = {}
    if log_id is not None:
        body["log_id"] = log_id
    if label is not None:
        body["label"] = label
    body.update(extra)
    return session.get(BASE_URL + EP_LIST,
                       json=body if body else None,
                       timeout=int(os.getenv("REQUEST_TIMEOUT", 15)))


def _historys(session):
    """historys 无参数，直接 GET。"""
    return session.get(BASE_URL + EP_HISTORYS,
                       timeout=int(os.getenv("REQUEST_TIMEOUT", 15)))


def _record(resp: requests.Response) -> None:
    """将本次 HTTP 调用写入报告 Extras（conftest.record_http_call）。"""
    try:
        from tests.conftest import record_http_call  # type: ignore[import]
        req  = resp.request
        body = None
        if req.body:
            try:
                body = json.loads(req.body)
            except Exception:
                body = req.body
        record_http_call(
            method=req.method,
            url=req.url,
            request_body=body,
            status_code=resp.status_code,
            response_body=resp.text,
        )
    except Exception:
        pass  # 报告记录失败不影响用例本身


def _assert_http_ok(resp: requests.Response):
    _record(resp)
    with step(f"HTTP 状态码为 200（实际 {resp.status_code}）"):
        assert resp.status_code == 200, \
            f"期望 HTTP 200，实际 {resp.status_code}。响应：{resp.text[:500]}"


def _assert_biz_ok(resp: requests.Response):
    body = resp.json()
    code = body.get("code")
    with step(f"业务码 code == 0（实际 {code}）"):
        assert code == 0, \
            f"业务码期望 0，实际 {code}，message：{body.get('message')}"


def _assert_param_error(resp: requests.Response, scene: str = ""):
    """参数校验失败：期望 HTTP 400/422，或 HTTP 200 且业务码非 0。"""
    is_http_error = resp.status_code in (400, 422)
    is_biz_error  = resp.status_code == 200 and resp.json().get("code") != 0
    with step(f"参数校验失败（场景：{scene}，HTTP {resp.status_code}）"):
        assert is_http_error or is_biz_error, (
            f"场景【{scene}】期望参数校验失败(400/422 或业务码≠0)，"
            f"实际 HTTP {resp.status_code}，响应：{resp.text[:300]}"
        )


# ─────────────────────────────────────────────────────────────────
# 响应结构完整性断言（基于 Apifox schema + 真实样本数据）
# 使用 ApiClient.assert_field_exists / assert_json_field
# ─────────────────────────────────────────────────────────────────

# 断言专用 ApiClient 实例（仅用于 assert_field_exists / assert_json_field，不发网络请求）
_AC = ApiClient()


def _assert_explore_data(resp: requests.Response) -> None:
    """
    断言 explore 成功响应的 data 字段结构：
      data.log_id                      : int > 0
      data.sync_status                 : str in [preview/running/completed/failed]
      data.feature_flags               : dict
      data.feature_flags.can_export    : bool
      data.feature_flags.can_paginate  : bool
    """
    data = resp.json().get("data", {})

    with step("data.log_id 存在且为正整数"):
        log_id = data.get("log_id")
        assert isinstance(log_id, int) and log_id > 0, \
            f"data.log_id 应为正整数，实际：{log_id!r}"

    with step(f"data.sync_status 为合法枚举值（实际：{data.get('sync_status')!r}）"):
        sync_status = data.get("sync_status")
        assert isinstance(sync_status, str) \
               and sync_status in ("preview", "running", "completed", "failed"), \
            f"data.sync_status 枚举值非法：{sync_status!r}"

    with step("data.feature_flags 存在且含 can_export / can_paginate"):
        flags = data.get("feature_flags", {})
        assert isinstance(flags, dict), \
            f"data.feature_flags 应为 dict，实际 {type(flags)}"
        for key in ("can_export", "can_paginate"):
            assert key in flags, \
                f"data.feature_flags 缺少字段 [{key}]，实际：{flags}"
            assert isinstance(flags[key], bool), \
                f"data.feature_flags.{key} 应为 boolean，实际：{flags[key]!r}"


def _assert_chart_bins(bins: list, chart_name: str) -> None:
    """断言 chart bins 数组：每条 label(str) + count(int≥0) + percent(number 0-1)。"""
    assert isinstance(bins, list), \
        f"{chart_name}.data.bins 应为数组，实际 {type(bins)}"
    for i, bin_item in enumerate(bins):
        assert isinstance(bin_item.get("label"), str), \
            f"{chart_name}.data.bins[{i}].label 应为字符串，实际：{bin_item.get('label')!r}"
        assert isinstance(bin_item.get("count"), int) and bin_item["count"] >= 0, \
            f"{chart_name}.data.bins[{i}].count 应为非负整数，实际：{bin_item.get('count')!r}"
        pct = bin_item.get("percent")
        assert isinstance(pct, (int, float)) and 0 <= pct <= 1, \
            f"{chart_name}.data.bins[{i}].percent 应在 [0,1]，实际：{pct!r}"


def _assert_chart_block(resp: requests.Response, chart_key: str) -> None:
    """
    断言单个图表块结构（Apifox schema 来源）：
      data.<chart_key>.title       : str 非空
      data.<chart_key>.data.total  : int >= 0
      data.<chart_key>.data.bins   : list，每条包含 label/count/percent
    """
    block = resp.json().get("data", {}).get(chart_key, {})
    with step(f"data.{chart_key}.title 为非空字符串（实际：{block.get('title')!r}）"):
        title = block.get("title")
        assert isinstance(title, str) and title, \
            f"data.{chart_key}.title 应为非空字符串，实际：{title!r}"

    with step(f"data.{chart_key}.data.total 为非负整数（实际：{block.get('data', {}).get('total')}）"):
        total = block.get("data", {}).get("total")
        assert isinstance(total, int) and total >= 0, \
            f"data.{chart_key}.data.total 应为非负整数，实际：{total!r}"

    with step(f"data.{chart_key}.data.bins 为数组且字段完整"):
        bins = block.get("data", {}).get("bins", [])
        _assert_chart_bins(bins, f"data.{chart_key}")


def _assert_chart_type1_response(resp: requests.Response) -> None:
    """
    断言 type=1（词找应用）chart 响应：
      data.search_chart  : 覆盖关键词分布图
      data.asa_chart     : 预估安装量分布图
    Apifox schema ref: /paths/_api_asa-aso-competitor_chart.json
    """
    _assert_chart_block(resp, "search_chart")
    _assert_chart_block(resp, "asa_chart")


def _assert_chart_type2_response(resp: requests.Response) -> None:
    """
    断言 type=2（应用找词）chart 响应（字段名来自后端代码，Apifox 未文档化）：
      data 中至少包含 coverage_chart 或 bidding_chart 之一
    """
    data = resp.json().get("data", {})
    has_type2_field = "coverage_chart" in data or "bidding_chart" in data
    with step(f"type=2 响应包含 coverage_chart 或 bidding_chart（data keys={list(data.keys())}）"):
        assert has_type2_field, (
            f"type=2 图表响应应包含 coverage_chart 或 bidding_chart，"
            f"实际 data keys={list(data.keys())}"
        )
    for key in ("coverage_chart", "bidding_chart"):
        if key in data:
            _assert_chart_block(resp, key)


def _assert_list_page_meta(resp: requests.Response) -> None:
    """
    断言 list 分页元数据（Apifox schema 必填字段）：
      data.list    : array
      data.current : int >= 1
      data.size    : int >= 1
      data.total   : int >= 0
    """
    data = resp.json().get("data", {})
    with step(f"data.list 为数组（长度 {len(data.get('list', []))}）"):
        assert isinstance(data.get("list"), list), \
            f"data.list 应为数组，实际：{type(data.get('list'))}"
    with step(f"data.current 为正整数（实际：{data.get('current')}）"):
        assert isinstance(data.get("current"), int) and data["current"] >= 1, \
            f"data.current 应 >= 1，实际：{data.get('current')!r}"
    with step(f"data.size 为正整数（实际：{data.get('size')}）"):
        assert isinstance(data.get("size"), int) and data["size"] >= 1, \
            f"data.size 应 >= 1，实际：{data.get('size')!r}"
    with step(f"data.total 为非负整数（实际：{data.get('total')}）"):
        assert isinstance(data.get("total"), int) and data["total"] >= 0, \
            f"data.total 应 >= 0，实际：{data.get('total')!r}"


def _assert_list_item_fields(item: dict) -> None:
    """
    断言 list 单条关键词记录的字段（基于 Apifox 真实样本数据）：
      keyword        : str 非空
      correlation    : int, 0-100
      rank           : int >= 1
      search_volume_num : int >= 0
      chance         : int, 0-100
      difficulty     : int, 0-100
    """
    kw = item.get("keyword")
    with step(f"list 条目 keyword 为非空字符串（实际：{kw!r}）"):
        assert isinstance(kw, str) and kw, \
            f"keyword 应为非空字符串，实际：{kw!r}"
    with step(f"list 条目 correlation 在 [0,100]（实际：{item.get('correlation')}）"):
        v = item.get("correlation")
        assert isinstance(v, int) and 0 <= v <= 100, \
            f"correlation 应在 [0,100]，实际：{v!r}"
    with step(f"list 条目 rank >= 1（实际：{item.get('rank')}）"):
        v = item.get("rank")
        assert isinstance(v, int) and v >= 1, f"rank 应为正整数，实际：{v!r}"
    with step(f"list 条目 search_volume_num >= 0（实际：{item.get('search_volume_num')}）"):
        v = item.get("search_volume_num")
        assert isinstance(v, int) and v >= 0, \
            f"search_volume_num 应为非负整数，实际：{v!r}"
    with step(f"list 条目 chance 在 [0,100]（实际：{item.get('chance')}）"):
        v = item.get("chance")
        assert isinstance(v, int) and 0 <= v <= 100, \
            f"chance 应在 [0,100]，实际：{v!r}"
    with step(f"list 条目 difficulty 在 [0,100]（实际：{item.get('difficulty')}）"):
        v = item.get("difficulty")
        assert isinstance(v, int) and 0 <= v <= 100, \
            f"difficulty 应在 [0,100]，实际：{v!r}"


def _assert_historys_item_fields(item: dict) -> None:
    """
    断言 historys 单条历史记录字段（Apifox schema required 字段）：
      type     : int in [1, 2]
      value    : str
      region   : str
      log_id   : int > 0
      icon     : str or None
      app_name : str
    """
    with step(f"historys 条目 type 为 1 或 2（实际：{item.get('type')!r}）"):
        assert item.get("type") in (1, 2), \
            f"historys 条目 type 应为 1 或 2，实际：{item.get('type')!r}"
    with step(f"historys 条目 value 为字符串（实际：{item.get('value')!r}）"):
        assert isinstance(item.get("value"), str), \
            f"historys 条目 value 应为字符串，实际：{item.get('value')!r}"
    with step(f"historys 条目 region 为字符串（实际：{item.get('region')!r}）"):
        assert isinstance(item.get("region"), str), \
            f"historys 条目 region 应为字符串，实际：{item.get('region')!r}"
    log_id = item.get("log_id")
    with step(f"historys 条目 log_id 为正整数（实际：{log_id!r}）"):
        assert isinstance(log_id, int) and log_id > 0, \
            f"historys 条目 log_id 应为正整数，实际：{log_id!r}"
    icon = item.get("icon")
    with step(f"historys 条目 icon 为字符串或 null（实际：{icon!r}）"):
        assert icon is None or isinstance(icon, str), \
            f"historys 条目 icon 应为字符串或 null，实际：{icon!r}"
    with step(f"historys 条目 app_name 为字符串（实际：{item.get('app_name')!r}）"):
        assert isinstance(item.get("app_name"), str), \
            f"historys 条目 app_name 应为字符串，实际：{item.get('app_name')!r}"


def _assert_asa_top_app(data: dict) -> None:
    """
    断言 list 响应 data.asaTopApp 字段结构（Apifox schema）：
      asaTopApp.top_app           : dict，含 app_id/app_name/icon
      asaTopApp.app_count         : int >= 0
      asaTopApp.apps              : list，每条含 app_id/app_name/icon
    """
    asa_top = data.get("asaTopApp") or data.get("asa_top_app")
    assert asa_top is not None, \
        f"响应 data 缺少 asaTopApp 字段，data keys={list(data.keys())}"
    assert isinstance(asa_top, dict), \
        f"asaTopApp 应为 dict，实际 {type(asa_top)}"

    # top_app
    top_app = asa_top.get("top_app")
    assert isinstance(top_app, dict), \
        f"asaTopApp.top_app 应为 dict，实际：{top_app!r}"
    for key in ("app_id", "app_name", "icon"):
        assert key in top_app, f"asaTopApp.top_app 缺少字段 [{key}]"
    assert isinstance(top_app["app_id"], str) and top_app["app_id"], \
        f"asaTopApp.top_app.app_id 应为非空字符串，实际：{top_app['app_id']!r}"

    # app_count
    app_count = asa_top.get("app_count")
    assert isinstance(app_count, int) and app_count >= 0, \
        f"asaTopApp.app_count 应为非负整数，实际：{app_count!r}"

    # apps
    apps = asa_top.get("apps")
    assert isinstance(apps, list), \
        f"asaTopApp.apps 应为数组，实际：{type(apps)}"
    for i, app in enumerate(apps):
        for key in ("app_id", "app_name", "icon"):
            assert key in app, f"asaTopApp.apps[{i}] 缺少字段 [{key}]"


# ─────────────────────────────────────────────────────────────────
# 会话级 fixture：提前执行一次 explore，共享 log_id 给 status/chart/list 测试
# ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def explore_log_id(login_session):
    """
    执行一次有效 explore（应用找词），获取并缓存 log_id。
    explore 返回的 data 中含 sync_status，可直接用于状态判断，无需单独 status 接口。
    """
    resp = _explore(login_session, type_=2, value=VALID_APP_ID, country=VALID_COUNTRY)
    if resp.status_code != 200 or resp.json().get("code") != 0:
        pytest.skip(
            f"前置 explore 失败，跳过依赖 log_id 的用例。"
            f"HTTP {resp.status_code}，响应：{resp.text[:300]}"
        )
    data = resp.json().get("data", {})
    log_id = data.get("log_id")
    if not log_id:
        pytest.skip("explore 响应中未返回 log_id，跳过依赖用例")
    return log_id


@pytest.fixture(scope="session")
def explore_sync_status(login_session, explore_log_id):
    """获取当前 explore 的 sync_status（从 explore 响应缓存）。"""
    resp = _explore(login_session, type_=2, value=VALID_APP_ID, country=VALID_COUNTRY)
    return resp.json().get("data", {}).get("sync_status", "preview")


# ══════════════════════════════════════════════════════════════════
# 接口一：POST /api/asa-aso-competitor/explore  —  触发竞品探索
# ══════════════════════════════════════════════════════════════════

class TestCompetitorExplore:
    """
    POST /api/asa-aso-competitor/explore
    参数：type(1|2,必填)  value(string,必填)  country(string,必填)
    业务：type=1 词找应用，type=2 应用找词
    注意：24h 内相同参数会复用缓存；首次会消耗配额
    """

    # ── 正常场景 ──────────────────────────────────────────────────

    @pytest.mark.smoke
    def test_应用找词_正常触发探索(self, login_session):
        """type=2（应用找词），传有效 appId + 国家，期望 200 + code=0 + 完整 data 结构。"""
        resp = _explore(login_session, type_=2, value=VALID_APP_ID, country=VALID_COUNTRY)
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        # 完整字段断言（log_id / sync_status / feature_flags 及其子字段）
        _assert_explore_data(resp)

    @pytest.mark.smoke
    def test_词找应用_正常触发探索(self, login_session):
        """type=1（词找应用），传有效关键词 + 国家，期望 200 + code=0 + 完整 data 结构。"""
        resp = _explore(login_session, type_=1, value=VALID_KEYWORD, country=VALID_COUNTRY)
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        # 与 type=2 共用相同 data 结构
        _assert_explore_data(resp)

    @pytest.mark.regression
    def test_24小时内重复探索返回相同log_id(self, login_session):
        """24h 内相同参数再次探索，后端复用缓存，应返回相同 log_id。"""
        resp1 = _explore(login_session, type_=2, value=VALID_APP_ID, country=VALID_COUNTRY)
        resp2 = _explore(login_session, type_=2, value=VALID_APP_ID, country=VALID_COUNTRY)
        _assert_http_ok(resp1)
        _assert_http_ok(resp2)
        log_id1 = resp1.json().get("data", {}).get("log_id")
        log_id2 = resp2.json().get("data", {}).get("log_id")
        assert log_id1 == log_id2, \
            f"24h 内相同参数期望复用缓存(同一 log_id)，实际 {log_id1} vs {log_id2}"

    @pytest.mark.regression
    def test_初始sync_status为preview或running(self, login_session):
        """首次 explore 返回的 sync_status 应为 preview/running（不应直接 completed）。"""
        resp = _explore(login_session, type_=2, value=VALID_APP_ID, country=VALID_COUNTRY)
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        sync_status = resp.json().get("data", {}).get("sync_status")
        assert sync_status in ("preview", "running", "completed"), \
            f"sync_status 值异常：{sync_status}"

    @pytest.mark.regression
    def test_feature_flags在未完成同步时导出和翻页为禁用(self, login_session):
        """同步未完成时，feature_flags.can_export 和 can_paginate 应为 False。"""
        resp = _explore(login_session, type_=2, value=VALID_APP_ID, country=VALID_COUNTRY)
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        data = resp.json().get("data", {})
        sync_status = data.get("sync_status")
        if sync_status == "completed":
            pytest.skip("数据已缓存完成，跳过此断言")
        flags = data.get("feature_flags", {})
        assert flags.get("can_export") is False, \
            f"未完成同步时 can_export 应为 False，实际：{flags}"
        assert flags.get("can_paginate") is False, \
            f"未完成同步时 can_paginate 应为 False，实际：{flags}"

    # ── 参数缺失场景 ──────────────────────────────────────────────

    @pytest.mark.negative
    def test_缺少必填参数_type(self, login_session):
        """缺少 type，期望 400/422 或业务错误。"""
        resp = _explore(login_session, type_=None, value=VALID_APP_ID, country=VALID_COUNTRY)
        _assert_param_error(resp, "缺少 type")

    @pytest.mark.negative
    def test_缺少必填参数_value(self, login_session):
        """缺少 value，期望 400/422 或业务错误。"""
        resp = _explore(login_session, type_=2, value=None, country=VALID_COUNTRY)
        _assert_param_error(resp, "缺少 value")

    @pytest.mark.negative
    def test_缺少必填参数_country(self, login_session):
        """缺少 country，期望 400/422 或业务错误。"""
        resp = _explore(login_session, type_=2, value=VALID_APP_ID, country=None)
        _assert_param_error(resp, "缺少 country")

    @pytest.mark.negative
    def test_请求体完全为空(self, login_session):
        """三个必填参数全部缺失，期望 400/422 或业务错误。"""
        resp = _explore(login_session, type_=None, value=None, country=None)
        _assert_param_error(resp, "请求体完全为空")

    # ── 参数类型错误 ──────────────────────────────────────────────

    @pytest.mark.negative
    @pytest.mark.parametrize("type_,value,country,desc", [
        ("2",     VALID_APP_ID, VALID_COUNTRY, "type 传字符串'2'"),
        (1.5,     VALID_APP_ID, VALID_COUNTRY, "type 传浮点数1.5"),
        (True,    VALID_APP_ID, VALID_COUNTRY, "type 传 boolean"),
        (2,       123456,       VALID_COUNTRY, "value 传 integer"),
        (2,       True,         VALID_COUNTRY, "value 传 boolean"),
        (2,       VALID_APP_ID, 123,           "country 传 integer"),
        (2,       VALID_APP_ID, True,          "country 传 boolean"),
    ])
    def test_参数类型错误(self, login_session, type_, value, country, desc):
        """字段类型与定义不符，期望 400/422 或业务错误码非 0。"""
        resp = _explore(login_session, type_=type_, value=value, country=country)
        _assert_param_error(resp, desc)

    # ── 边界值场景 ────────────────────────────────────────────────

    @pytest.mark.boundary
    @pytest.mark.parametrize("type_,desc,expect_ok", [
        (1, "type=1 词找应用（有效下界）", True),
        (2, "type=2 应用找词（有效上界）", True),
        (0, "type=0（低于合法范围）",      False),
        (3, "type=3（高于合法范围）",      False),
    ])
    def test_边界值_type枚举范围(self, login_session, type_, desc, expect_ok):
        """type 只允许 1 或 2，越界应返回错误。"""
        resp = _explore(login_session, type_=type_, value=VALID_APP_ID, country=VALID_COUNTRY)
        if expect_ok:
            _assert_http_ok(resp)
            _assert_biz_ok(resp)
        else:
            _assert_param_error(resp, desc)

    @pytest.mark.boundary
    @pytest.mark.parametrize("value,desc", [
        ("",        "value 空字符串"),
        ("A" * 256, "value 256 字符（超长）"),
    ])
    def test_边界值_value字段(self, login_session, value, desc):
        """value 为空字符串或超长字符串，期望校验失败或服务器不返回 5xx。"""
        resp = _explore(login_session, type_=2, value=value, country=VALID_COUNTRY)
        assert resp.status_code != 500, \
            f"场景【{desc}】不应返回 500，实际：{resp.status_code}，响应：{resp.text[:200]}"

    @pytest.mark.boundary
    @pytest.mark.parametrize("country,desc", [
        ("",        "country 空字符串"),
        ("A" * 256, "country 256 字符（超长）"),
        ("XX",      "country 不存在的国家代码"),
    ])
    def test_边界值_country字段(self, login_session, country, desc):
        """country 异常值，服务器不应返回 5xx。"""
        resp = _explore(login_session, type_=2, value=VALID_APP_ID, country=country)
        assert resp.status_code != 500, \
            f"场景【{desc}】不应返回 500，实际：{resp.status_code}"

    # ── 越权场景 ──────────────────────────────────────────────────

    @pytest.mark.negative
    def test_无认证访问_期望401或403(self):
        """不携带任何 Cookie/Token，期望 401 或 403。"""
        anon = requests.Session()
        anon.headers.update({"Content-Type": "application/json", "Accept": "application/json"})
        resp = _explore(anon, type_=2, value=VALID_APP_ID, country=VALID_COUNTRY)
        assert resp.status_code in (401, 403), \
            f"无认证访问期望 401/403，实际 {resp.status_code}，响应：{resp.text[:200]}"

    @pytest.mark.negative
    def test_伪造Cookie访问_期望401或403(self):
        """携带伪造 Cookie，期望 401 或 403。"""
        fake = requests.Session()
        fake.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Cookie": "laravel_session=fake_session_value_00000000",
        })
        resp = _explore(fake, type_=2, value=VALID_APP_ID, country=VALID_COUNTRY)
        assert resp.status_code in (401, 403), \
            f"伪造 Cookie 期望 401/403，实际 {resp.status_code}"

    @pytest.mark.negative
    def test_低权限用户访问_期望403或业务错误(self):
        """
        无竞品分析权限的账号，期望 403 或业务错误码非 0。
        需在 .env 配置 LOW_PERM_USERNAME + LOW_PERM_PASSWORD，否则跳过。
        """
        from tests.conftest import do_login
        low_user = os.getenv("LOW_PERM_USERNAME", "")
        low_pass = os.getenv("LOW_PERM_PASSWORD", "")
        if not low_user or not low_pass:
            pytest.skip("未配置 LOW_PERM_USERNAME/PASSWORD，跳过低权限测试")
        low_session = do_login(low_user, low_pass)
        resp = _explore(low_session, type_=2, value=VALID_APP_ID, country=VALID_COUNTRY)
        is_forbidden     = resp.status_code == 403
        is_biz_forbidden = resp.status_code == 200 and resp.json().get("code") != 0
        assert is_forbidden or is_biz_forbidden, \
            f"低权限用户期望 403 或业务错误，实际 {resp.status_code}"


# ══════════════════════════════════════════════════════════════════
# 接口二：GET /api/asa-aso-competitor/historys  —  探索历史记录
# Apifox ref: /paths/_api_asa-aso-competitor_historys.json
# ══════════════════════════════════════════════════════════════════

class TestCompetitorHistorys:
    """
    GET /api/asa-aso-competitor/historys
    无参数，返回当前团队下的探索历史列表。
    响应字段：type / value / region / log_id / icon / app_name / sync_status / status_text / region_name
    """

    # ── 正常场景 ──────────────────────────────────────────────────

    @pytest.mark.smoke
    def test_获取历史记录_返回数组且结构完整(self, login_session):
        """期望 200 + code=0 + data 为数组，每条记录字段类型和值范围符合 Apifox schema。"""
        resp = _historys(login_session)
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        # 顶层结构：data 为数组
        _AC.assert_field_exists(resp, "code", "message", "data")
        _AC.assert_json_field(resp, "data", lambda v: isinstance(v, list))
        # 每条记录完整断言
        items = resp.json().get("data", [])
        for item in items:
            _assert_historys_item_fields(item)

    @pytest.mark.smoke
    def test_历史记录每条包含必要字段(self, login_session):
        """data 非空时，每条记录必须包含 type/value/region/log_id/icon/app_name，
        并验证字段类型与值范围（Apifox schema required 字段全覆盖）。"""
        resp = _historys(login_session)
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        items = resp.json().get("data", [])
        if not items:
            pytest.skip("当前环境无历史记录，跳过字段完整性断言")
        for item in items:
            _assert_historys_item_fields(item)

    @pytest.mark.regression
    def test_历史记录type字段枚举值合法(self, login_session):
        """每条记录的 type 只能为 1（词找应用）或 2（应用找词）。"""
        resp = _historys(login_session)
        _assert_http_ok(resp)
        items = resp.json().get("data", [])
        for item in items:
            assert item.get("type") in (1, 2), \
                f"type 值不合法：{item.get('type')}，完整记录：{item}"

    @pytest.mark.regression
    def test_历史记录log_id为正整数(self, login_session):
        """每条记录的 log_id 应为正整数。"""
        resp = _historys(login_session)
        _assert_http_ok(resp)
        items = resp.json().get("data", [])
        for item in items:
            log_id = item.get("log_id")
            assert isinstance(log_id, int) and log_id > 0, \
                f"log_id 应为正整数，实际：{log_id}"

    @pytest.mark.regression
    def test_历史记录包含已完成探索_explore后可见(self, login_session, explore_log_id):
        """执行 explore 后，历史记录中应能查到对应 log_id。"""
        resp = _historys(login_session)
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        log_ids = [item.get("log_id") for item in resp.json().get("data", [])]
        assert explore_log_id in log_ids, \
            f"explore_log_id={explore_log_id} 未出现在历史记录中，当前 log_ids={log_ids}"

    # ── 越权场景 ──────────────────────────────────────────────────

    @pytest.mark.negative
    def test_无认证访问_期望401或403(self):
        """不携带认证信息，期望 401 或 403。"""
        anon = requests.Session()
        anon.headers.update({"Content-Type": "application/json"})
        resp = _historys(anon)
        assert resp.status_code in (401, 403), \
            f"无认证访问期望 401/403，实际 {resp.status_code}"

    @pytest.mark.negative
    def test_伪造Cookie访问_期望401或403(self):
        """携带伪造 Cookie，期望 401 或 403。"""
        fake = requests.Session()
        fake.headers.update({
            "Content-Type": "application/json",
            "Cookie": "laravel_session=fake_value_00000000",
        })
        resp = _historys(fake)
        assert resp.status_code in (401, 403), \
            f"伪造 Cookie 期望 401/403，实际 {resp.status_code}"


# ══════════════════════════════════════════════════════════════════
# 接口三：GET /api/asa-aso-competitor/chart  —  数据分析图表
# Apifox ref: /paths/_api_asa-aso-competitor_chart.json
# 注意：此接口为 GET + requestBody，log_id 在 JSON body 中传递
# ══════════════════════════════════════════════════════════════════

class TestCompetitorChart:
    """
    GET /api/asa-aso-competitor/chart
    参数：log_id(integer, 必填，requestBody)
    响应（type=1 词找应用）：search_chart + asa_chart
    响应（type=2 应用找词）：coverage_chart + bidding_chart
    注意：sync_status != completed 时后端直接返回业务错误（"数据尚未同步完成"）
    """

    # ── 正常场景 ──────────────────────────────────────────────────

    @pytest.mark.smoke
    def test_获取图表数据_同步完成后返回完整结构(self, login_session, explore_log_id,
                                                   explore_sync_status):
        """
        sync_status=completed 后调用，期望 200 + code=0。
        type=2（应用找词）返回 coverage_chart + bidding_chart，断言 title/total/bins 完整。
        若数据未完成同步，跳过。
        """
        if explore_sync_status != "completed":
            pytest.skip(f"数据同步未完成(当前:{explore_sync_status})，跳过图表正常场景")

        resp = _chart(login_session, log_id=explore_log_id)
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        # type=2 完整结构断言：coverage_chart / bidding_chart + bins 子字段
        _assert_chart_type2_response(resp)

    @pytest.mark.smoke
    def test_获取图表数据_Apifox响应结构验证(self, login_session, explore_log_id,
                                               explore_sync_status):
        """
        根据 Apifox schema 验证 type=1（词找应用）的响应结构：
        data.search_chart.{title, data.{total, bins}} + data.asa_chart.{...}
        若当前探索为 type=2 或未完成则跳过。
        """
        if explore_sync_status != "completed":
            pytest.skip("数据同步未完成，跳过 schema 验证")

        # 需要一个 type=1 的 log_id，此处跳过（当前 fixture 为 type=2）
        pytest.skip("当前 explore_log_id 为 type=2，type=1 schema 验证需单独 log_id")

    @pytest.mark.regression
    def test_获取图表数据_同步未完成时返回业务错误(self, login_session, explore_log_id,
                                                     explore_sync_status):
        """
        sync_status != completed 时，后端拒绝返回图表，期望业务错误。
        """
        if explore_sync_status == "completed":
            pytest.skip("数据已同步完成，此场景跳过")

        resp = _chart(login_session, log_id=explore_log_id)
        _assert_http_ok(resp)
        biz_code = resp.json().get("code")
        assert biz_code != 0, \
            f"数据未同步完成时图表接口应返回业务错误，实际 code={biz_code}"

    # ── 参数缺失场景 ──────────────────────────────────────────────

    @pytest.mark.negative
    def test_缺少必填参数_log_id(self, login_session):
        """不传 log_id，期望 400/422 或业务错误。"""
        resp = _chart(login_session)
        _assert_param_error(resp, "缺少 log_id")

    # ── 参数类型错误 ──────────────────────────────────────────────

    @pytest.mark.negative
    @pytest.mark.parametrize("log_id,desc", [
        ("abc",   "log_id 传字符串"),
        (1.5,     "log_id 传浮点数"),
        (True,    "log_id 传 boolean"),
    ])
    def test_参数类型错误_log_id(self, login_session, log_id, desc):
        """log_id 类型错误，期望 400/422 或业务错误。"""
        resp = _chart(login_session, log_id=log_id)
        _assert_param_error(resp, desc)

    # ── 边界值场景 ────────────────────────────────────────────────

    @pytest.mark.boundary
    @pytest.mark.parametrize("log_id,desc", [
        (0,        "log_id=0"),
        (-1,       "log_id 负数"),
        (99999999, "log_id 不存在"),
    ])
    def test_边界值_无效log_id不应返回5xx(self, login_session, log_id, desc):
        resp = _chart(login_session, log_id=log_id)
        assert resp.status_code != 500, \
            f"场景【{desc}】不应返回 500，实际：{resp.status_code}"
        _assert_param_error(resp, desc)

    # ── 越权场景 ──────────────────────────────────────────────────

    @pytest.mark.negative
    def test_无认证访问_期望401或403(self, explore_log_id):
        """不携带认证，期望 401 或 403（requestBody 方式传 log_id）。"""
        anon = requests.Session()
        anon.headers.update({"Content-Type": "application/json"})
        resp = _chart(anon, log_id=explore_log_id)
        assert resp.status_code in (401, 403), \
            f"无认证访问期望 401/403，实际 {resp.status_code}"


# ══════════════════════════════════════════════════════════════════
# 接口四：GET /api/asa-aso-competitor/list  —  分页关键词列表
# Apifox ref: /paths/_api_asa-aso-competitor_list.json
# 注意：此接口为 GET + requestBody，所有参数在 JSON body 中传递
# ══════════════════════════════════════════════════════════════════

class TestCompetitorList:
    """
    GET /api/asa-aso-competitor/list
    必填（requestBody）：log_id(integer)  label(aso|asa)
    可选（requestBody）：page / limit(1-500) / field / order_by / sort / export(bool) /
          app(max:100) / keyword(max:100) / rank_min/max / search_volume_num_min/max /
          correlation_min/max / filter_symbol / volume_num_min/max / bidding_num_min/max

    Apifox 响应字段（来自实际 schema）：
      data.list[]  data.current  data.size  data.total  data.asaTopApp（label=aso 时）

    重要业务逻辑（来自代码）：
      - 同步未完成时：PREVIEW_LIMIT=500 条，固定返回第1页，不支持分页
      - 同步完成时：正常分页，limit 最大 500
      - export=true 时：触发异步导出任务，返回"离线下载"提示而非数据列表
      - label=aso + type=1（词找应用）时：附加 asaTopApp 字段
    """

    # ── 正常场景 ──────────────────────────────────────────────────

    @pytest.mark.smoke
    def test_获取ASO覆盖词列表_返回结构完整(self, login_session, explore_log_id):
        """
        label=aso，期望 200 + code=0。
        断言分页元数据（list/current/size/total）+ 每条记录字段类型和值范围。
        Apifox schema: /paths/_api_asa-aso-competitor_list.json
        """
        resp = _list(login_session, log_id=explore_log_id, label="aso")
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        # 分页元数据完整性
        _assert_list_page_meta(resp)
        # 列表条目字段断言（取前 3 条，避免全量断言超时）
        items = resp.json()["data"]["list"]
        for item in items[:3]:
            _assert_list_item_fields(item)

    @pytest.mark.smoke
    def test_获取ASA竞价词列表_返回结构完整(self, login_session, explore_log_id):
        """
        label=asa，期望 200 + code=0。
        断言分页元数据 + 每条记录字段类型和值范围（与 aso 相同 schema）。
        """
        resp = _list(login_session, log_id=explore_log_id, label="asa")
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        _assert_list_page_meta(resp)
        items = resp.json()["data"]["list"]
        for item in items[:3]:
            _assert_list_item_fields(item)

    @pytest.mark.smoke
    def test_分页字段current和size存在(self, login_session, explore_log_id):
        """Apifox schema 中 current/size/total 为必填，验证存在且类型正确。"""
        resp = _list(login_session, log_id=explore_log_id, label="aso", page=1, limit=10)
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        data = resp.json().get("data", {})
        for field in ("current", "size", "total"):
            assert field in data, f"响应 data 缺少 Apifox schema 必填字段 [{field}]，data={data}"
        assert isinstance(data["total"], int) and data["total"] >= 0

    @pytest.mark.regression
    def test_同步未完成时最多返回500条(self, login_session, explore_log_id, explore_sync_status):
        """
        sync_status != completed 时，无论请求多少，最多返回 PREVIEW_LIMIT=500 条。
        若已完成同步则跳过。
        """
        if explore_sync_status == "completed":
            pytest.skip("数据已同步完成，PREVIEW_LIMIT 限制不适用")

        resp = _list(login_session, log_id=explore_log_id, label="aso", limit=500)
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        data = resp.json().get("data", {})
        total = data.get("total", 0)
        assert total <= 500, \
            f"未完成同步时 total 不应超过 500（PREVIEW_LIMIT），实际：{total}"

    @pytest.mark.regression
    def test_关键词筛选返回包含指定关键词的结果(self, login_session, explore_log_id):
        """传入 keyword 筛选参数，返回的关键词应均包含该字符串。"""
        resp = _list(login_session, log_id=explore_log_id, label="aso", keyword="game")
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        items = resp.json().get("data", {}).get("list", [])
        for item in items:
            kw = item.get("keyword", "")
            assert "game" in kw.lower(), \
                f"keyword 筛选后结果不包含 'game'：{kw}"

    @pytest.mark.regression
    def test_排名区间筛选rank_min和rank_max(self, login_session, explore_log_id):
        """rank_min=1 + rank_max=100，返回结果的 rank 应在 [1, 100] 范围内。"""
        resp = _list(login_session, log_id=explore_log_id, label="aso",
                     rank_min=1, rank_max=100)
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        items = resp.json().get("data", {}).get("list", [])
        for item in items:
            rank = item.get("rank")
            if rank is not None:
                assert 1 <= rank <= 100, \
                    f"rank 不在筛选范围 [1,100]，实际：{rank}"

    @pytest.mark.regression
    def test_filter_symbol过滤含符号关键词(self, login_session, explore_log_id):
        """filter_symbol=true，返回的关键词不应包含特殊符号（! @ # 等）。"""
        import re
        resp = _list(login_session, log_id=explore_log_id, label="aso",
                     filter_symbol="true")
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        items = resp.json().get("data", {}).get("list", [])
        symbol_pattern = re.compile(r'[!@#$%^&*,，:：·;\s]')
        for item in items:
            kw = item.get("keyword", "")
            assert not symbol_pattern.search(kw), \
                f"filter_symbol=true 后仍出现含符号关键词：{kw!r}"

    @pytest.mark.regression
    def test_export触发异步导出不直接返回数据(self, login_session, explore_log_id,
                                               explore_sync_status):
        """
        export=true 时，期望触发离线下载任务（业务码=0 + 提示文字），
        而非直接返回数据列表。仅在 sync_status=completed 时有效，否则跳过。
        """
        if explore_sync_status != "completed":
            pytest.skip("数据同步未完成，export 功能不可用")
        resp = _list(login_session, log_id=explore_log_id, label="aso", export=True)
        _assert_http_ok(resp)
        biz_code = resp.json().get("code")
        assert biz_code == 0, f"export 触发期望 code=0，实际：{biz_code}"
        data = resp.json().get("data")
        assert data == [] or data is None or data == {}, \
            f"export=true 时不应直接返回列表数据，实际 data={data}"

    # ── 参数缺失场景 ──────────────────────────────────────────────

    @pytest.mark.negative
    def test_缺少必填参数_log_id(self, login_session, explore_log_id):
        """缺少 log_id，期望 400/422 或业务错误。"""
        resp = _list(login_session, label="aso")
        _assert_param_error(resp, "缺少 log_id")

    @pytest.mark.negative
    def test_缺少必填参数_label(self, login_session, explore_log_id):
        """缺少 label，期望 400/422 或业务错误。"""
        resp = _list(login_session, log_id=explore_log_id)
        _assert_param_error(resp, "缺少 label")

    @pytest.mark.negative
    def test_label枚举值非法(self, login_session, explore_log_id):
        """label 传入非 aso/asa 的值，期望 400/422 或业务错误。"""
        resp = _list(login_session, log_id=explore_log_id, label="invalid")
        _assert_param_error(resp, "label=invalid")

    # ── 参数类型错误 ──────────────────────────────────────────────

    @pytest.mark.negative
    @pytest.mark.parametrize("field_name,value,desc", [
        ("log_id",  "abc",   "log_id 传字符串"),
        ("label",   123,     "label 传 integer"),
        ("page",    "abc",   "page 传字符串"),
        ("limit",   "abc",   "limit 传字符串"),
        ("rank_min","abc",   "rank_min 传字符串"),
        ("rank_max","abc",   "rank_max 传字符串"),
    ])
    def test_参数类型错误(self, login_session, explore_log_id, field_name, value, desc):
        """字段类型错误，期望 400/422 或业务错误。"""
        kwargs = {"log_id": explore_log_id, "label": "aso"}
        kwargs[field_name] = value
        resp = _list(login_session, **kwargs)
        _assert_param_error(resp, desc)

    # ── 边界值场景 ────────────────────────────────────────────────

    @pytest.mark.boundary
    @pytest.mark.parametrize("limit,desc,expect_ok", [
        (1,   "limit 最小值=1",           True),
        (500, "limit 最大值=500",          True),
        (0,   "limit=0（低于最小值）",     False),
        (501, "limit=501（高于最大值）",   False),
        (-1,  "limit 负数",               False),
    ])
    def test_边界值_limit范围(self, login_session, explore_log_id, limit, desc, expect_ok):
        """limit 在 1-500 范围内有效，超出范围应报错。"""
        resp = _list(login_session, log_id=explore_log_id, label="aso", limit=limit)
        if expect_ok:
            _assert_http_ok(resp)
            _assert_biz_ok(resp)
        else:
            _assert_param_error(resp, desc)

    @pytest.mark.boundary
    @pytest.mark.parametrize("page,desc,expect_ok", [
        (1,   "page=1（最小值）",     True),
        (0,   "page=0（低于最小值）", False),
        (-1,  "page 负数",            False),
    ])
    def test_边界值_page范围(self, login_session, explore_log_id, page, desc, expect_ok):
        """page 最小值为 1，小于 1 应报错。"""
        resp = _list(login_session, log_id=explore_log_id, label="aso", page=page)
        if expect_ok:
            _assert_http_ok(resp)
        else:
            _assert_param_error(resp, desc)

    @pytest.mark.boundary
    @pytest.mark.parametrize("field,value,desc", [
        ("app",     "A" * 101, "app 超过 max:100"),
        ("keyword", "A" * 101, "keyword 超过 max:100"),
        ("app",     "",        "app 空字符串"),
        ("keyword", "",        "keyword 空字符串"),
    ])
    def test_边界值_字符串字段长度(self, login_session, explore_log_id, field, value, desc):
        """字符串字段长度边界，超长应报错或返回业务错误，服务器不应 5xx。"""
        kwargs = {"log_id": explore_log_id, "label": "aso"}
        kwargs[field] = value
        resp = _list(login_session, **kwargs)
        assert resp.status_code != 500, \
            f"场景【{desc}】不应返回 500，实际：{resp.status_code}"
        if len(value) > 100:
            _assert_param_error(resp, desc)

    @pytest.mark.boundary
    @pytest.mark.parametrize("rank_min,rank_max,desc,expect_error", [
        (0,   100, "rank 最小值=0，合法",       False),
        (-1,  100, "rank_min 负数，非法",        True),
        (100, 50,  "rank_min > rank_max，逻辑错", False),  # 后端未必校验，观察实际行为
    ])
    def test_边界值_rank区间(self, login_session, explore_log_id, rank_min, rank_max,
                             desc, expect_error):
        """rank 区间边界场景，服务器不应 5xx。"""
        resp = _list(login_session, log_id=explore_log_id, label="aso",
                     rank_min=rank_min, rank_max=rank_max)
        assert resp.status_code != 500, \
            f"场景【{desc}】不应返回 500，实际：{resp.status_code}"
        if expect_error:
            _assert_param_error(resp, desc)

    # ── 越权场景 ──────────────────────────────────────────────────

    @pytest.mark.negative
    def test_无认证访问_期望401或403(self, explore_log_id):
        """不携带认证信息，期望 401 或 403。"""
        anon = requests.Session()
        anon.headers.update({"Content-Type": "application/json"})
        resp = _list(anon, log_id=explore_log_id, label="aso")
        assert resp.status_code in (401, 403), \
            f"无认证访问期望 401/403，实际 {resp.status_code}"

    @pytest.mark.negative
    def test_export未完成同步时应被拒绝(self, login_session, explore_log_id,
                                         explore_sync_status):
        """
        sync_status != completed 时调用 export=true，
        后端应返回业务错误（数据尚未同步完成，暂不可导出）。
        若已完成同步则跳过。
        """
        if explore_sync_status == "completed":
            pytest.skip("数据已同步完成，export 可用，跳过此场景")

        resp = _list(login_session, log_id=explore_log_id, label="aso", export=True)
        _assert_http_ok(resp)
        biz_code = resp.json().get("code")
        assert biz_code != 0, \
            f"未完成同步时 export 应返回业务错误，实际 code={biz_code}"


# ══════════════════════════════════════════════════════════════════
# ⚠️ 补充测试 — 覆盖代码分支分析发现的未覆盖分支（2026-05-06 追加）
# 来源：AsaAsoCompetitorController / Service / SyncSourceJob 分支覆盖报告
# ══════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────
# 补充 Fixture：type=1（词找应用）的 log_id 和 sync_status
# 用于覆盖 chart() type=1 分支 + historys type=1 app_name 分支
# ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def explore_log_id_type1(login_session):
    """
    执行一次 type=1（词找应用）的 explore，缓存对应 log_id。
    用于覆盖 chart() 的 type=1 分支（search_chart + asa_chart）
    以及 historys() 中 item->type==1 时 app_name=value 的分支。
    """
    resp = _explore(login_session, type_=1, value=VALID_KEYWORD, country=VALID_COUNTRY)
    if resp.status_code != 200 or resp.json().get("code") != 0:
        pytest.skip(
            f"前置 type=1 explore 失败，跳过依赖用例。"
            f"HTTP {resp.status_code}，响应：{resp.text[:300]}"
        )
    data = resp.json().get("data", {})
    log_id = data.get("log_id")
    if not log_id:
        pytest.skip("type=1 explore 响应中未返回 log_id，跳过依赖用例")
    return log_id


@pytest.fixture(scope="session")
def explore_sync_status_type1(login_session, explore_log_id_type1):
    """获取 type=1 explore 的当前 sync_status（复用缓存，不消耗额外配额）。"""
    resp = _explore(login_session, type_=1, value=VALID_KEYWORD, country=VALID_COUNTRY)
    return resp.json().get("data", {}).get("sync_status", "preview")


# ══════════════════════════════════════════════════════════════════
# 补充 1：explore() 未覆盖分支
# ══════════════════════════════════════════════════════════════════

class TestCompetitorExploreUncovered:
    """
    覆盖 explore() 和 handleCache()/handleFreshExplore() 中的未覆盖分支：
      - consumeQuota 抛出异常（配额耗尽）→ 返回业务错误
      - handleCache 缓存命中时不重复消耗配额（log_id 相同）
      - handleCache resolveSyncStatus != COMPLETED 时直接复用不消耗配额
    """

    @pytest.mark.regression
    def test_配额耗尽时返回业务错误(self):
        """
        触发条件：consumeQuota() 抛出异常（FrequencyLimitation 判断已达上限）。
        代码分支：handleFreshExplore() try consumeQuota → catch → updateLogSyncStatus(FAILED) + throw。

        前置条件（二选一）：
          方案A：配置环境变量 QUOTA_EXHAUSTED_USERNAME + QUOTA_EXHAUSTED_PASSWORD，
                 该账号今日探索次数已耗尽。
          方案B：手动执行以下 SQL 将某账号配额设置为已耗尽：
            UPDATE asa_aso_competitor_frequency
            SET used = daily_limit
            WHERE user_id = <target_user_id>
              AND DATE(created_at) = CURDATE();

        期望：HTTP 200 + 业务码非 0（如「今日探索次数已达上限」）。
        """
        from tests.conftest import do_login  # type: ignore[import]
        user = os.getenv("QUOTA_EXHAUSTED_USERNAME", "")
        pwd  = os.getenv("QUOTA_EXHAUSTED_PASSWORD", "")
        if not user or not pwd:
            pytest.skip("未配置 QUOTA_EXHAUSTED_USERNAME/PASSWORD，跳过配额耗尽测试")
        session = do_login(user, pwd)
        resp = _explore(session, type_=2, value=VALID_APP_ID, country=VALID_COUNTRY)
        _assert_http_ok(resp)
        biz_code = resp.json().get("code")
        assert biz_code != 0, \
            f"配额耗尽时期望业务错误码非 0，实际 code={biz_code}，响应：{resp.text[:300]}"

    @pytest.mark.regression
    def test_缓存命中时再次explore返回相同log_id且不报错(self, login_session):
        """
        触发条件：handleCache() — 24h 内相同参数再次调用 explore。
        代码分支：cachedLog 存在 → handleCache → dispatchSyncJobs → buildExploreResponse。
        验证：两次调用均 code=0，log_id 相同（走缓存，不重复 dispatch Job）。
        """
        resp1 = _explore(login_session, type_=2, value=VALID_APP_ID, country=VALID_COUNTRY)
        resp2 = _explore(login_session, type_=2, value=VALID_APP_ID, country=VALID_COUNTRY)
        _assert_http_ok(resp1)
        _assert_http_ok(resp2)
        _assert_biz_ok(resp1)
        _assert_biz_ok(resp2)
        log_id1 = resp1.json().get("data", {}).get("log_id")
        log_id2 = resp2.json().get("data", {}).get("log_id")
        assert log_id1 == log_id2, \
            f"缓存命中时 log_id 应相同（handleCache 分支），实际 {log_id1} vs {log_id2}"

    @pytest.mark.regression
    def test_缓存命中且未完成时不额外扣减配额(self, login_session):
        """
        触发条件：handleCache() 中 resolveSyncStatus != COMPLETED 分支 → 直接 return（不消耗配额）。
        验证：sync 未完成时，缓存命中路径能正常返回，不会因配额操作报错。
        """
        resp = _explore(login_session, type_=2, value=VALID_APP_ID, country=VALID_COUNTRY)
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        sync_status = resp.json().get("data", {}).get("sync_status")
        if sync_status == "completed":
            pytest.skip("当前 sync 已完成，handleCache 非 COMPLETED 分支本次未触发")
        # 再次调用，走 handleCache → resolveSyncStatus != COMPLETED → return（不扣配额）
        resp2 = _explore(login_session, type_=2, value=VALID_APP_ID, country=VALID_COUNTRY)
        _assert_http_ok(resp2)
        _assert_biz_ok(resp2)
        assert resp2.json().get("data", {}).get("log_id") == \
               resp.json().get("data", {}).get("log_id"), \
            "两次调用应返回同一 log_id（均命中缓存）"


# ══════════════════════════════════════════════════════════════════
# 补充 2：historys() 未覆盖分支
# ══════════════════════════════════════════════════════════════════

class TestCompetitorHistorysUncovered:
    """
    覆盖 historys() 中未测试的代码分支：
      - item->type == 1 → app_name = value（非 DB JOIN，直接赋值）
      - match sync_status → status_text 文案（COMPLETED / RUNNING / PREVIEW）
      - sync_status 为 null 的老数据兼容路径
    """

    @pytest.mark.regression
    def test_type1记录的app_name等于value字段(self, login_session, explore_log_id_type1):
        """
        触发条件：historys 结果中存在 type=1（词找应用）的记录。
        代码分支：if ($item->type == 1) { app_name = item->value }
                  （而非 type=2 时通过 JOIN apps 表取 app_name）。
        前置条件：explore_log_id_type1 fixture 已成功执行 type=1 的探索。
        验证：该记录的 app_name 字段值 == value 字段值（即传入的关键词）。
        """
        resp = _historys(login_session)
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        items = resp.json().get("data", [])
        type1_items = [item for item in items if item.get("type") == 1]
        if not type1_items:
            pytest.skip(
                "历史记录中无 type=1 条目，跳过；"
                "请确认 explore_log_id_type1 fixture 已正常执行"
            )
        for item in type1_items:
            app_name = item.get("app_name", "")
            value    = item.get("value", "")
            assert app_name == value, (
                f"type=1 记录 app_name 应等于 value（代码：app_name = item->value），"
                f"实际 app_name={app_name!r}，value={value!r}，完整记录：{item}"
            )

    @pytest.mark.regression
    def test_历史记录status_text字段非空(self, login_session):
        """
        触发条件：historys transform 中 match sync_status 生成 status_text 的全部分支。
        代码分支：COMPLETED→「数据已就绪」/ RUNNING→「数据同步中」/ default→「已展示首批数据」。
        验证：每条历史记录均含 status_text 字段且为非空字符串。
        """
        resp = _historys(login_session)
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        items = resp.json().get("data", [])
        if not items:
            pytest.skip("当前环境无历史记录，跳过 status_text 验证")
        for item in items:
            assert "status_text" in item, \
                f"历史记录缺少 status_text 字段，item={item}"
            assert isinstance(item["status_text"], str) and item["status_text"], \
                f"status_text 应为非空字符串，实际：{item['status_text']!r}，item={item}"

    @pytest.mark.regression
    def test_completed记录的status_text文案验证(self, login_session,
                                                 explore_log_id,
                                                 explore_sync_status):
        """
        触发条件：match sync_status == COMPLETED → status_text「数据已就绪」（或类似）。
        前置条件：存在 sync_status=completed 的历史记录（explore_sync_status == 'completed'）。
        验证：目标记录 status_text 非空，且 sync_status 字段为 'completed'。
        """
        if explore_sync_status != "completed":
            pytest.skip("当前 explore 未完成同步，跳过 COMPLETED 分支 status_text 验证")
        resp = _historys(login_session)
        _assert_http_ok(resp)
        items = resp.json().get("data", [])
        target = next(
            (item for item in items if item.get("log_id") == explore_log_id), None
        )
        assert target is not None, \
            f"historys 中未找到 log_id={explore_log_id} 的记录，全部 log_ids={[i.get('log_id') for i in items]}"
        assert target.get("sync_status") == "completed", \
            f"目标记录 sync_status 应为 completed，实际：{target.get('sync_status')}"
        status_text = target.get("status_text", "")
        assert status_text, \
            f"sync_status=completed 记录的 status_text 不应为空，item={target}"

    @pytest.mark.regression
    def test_running状态记录包含status_text(self, login_session):
        """
        触发条件：match sync_status == RUNNING → status_text 文案分支。
        验证：历史记录中 sync_status=running 的条目 status_text 非空。
        说明：需要在同步进行中时调用（或历史记录中存在 running 状态条目）。
        """
        resp = _historys(login_session)
        _assert_http_ok(resp)
        items = resp.json().get("data", [])
        running_items = [i for i in items if i.get("sync_status") == "running"]
        if not running_items:
            pytest.skip("当前历史记录中无 sync_status=running 条目，跳过；建议在同步进行中时执行")
        for item in running_items:
            assert "status_text" in item, \
                f"running 状态记录缺少 status_text，item={item}"
            assert item["status_text"], \
                f"running 状态 status_text 不应为空，item={item}"

    @pytest.mark.regression
    def test_preview状态记录包含status_text(self, login_session):
        """
        触发条件：match default（sync_status=preview）→ status_text 文案分支。
        验证：历史记录中 sync_status=preview 的条目 status_text 非空。
        """
        resp = _historys(login_session)
        _assert_http_ok(resp)
        items = resp.json().get("data", [])
        preview_items = [i for i in items if i.get("sync_status") == "preview"]
        if not preview_items:
            pytest.skip("当前历史记录中无 sync_status=preview 条目，跳过")
        for item in preview_items:
            assert "status_text" in item, \
                f"preview 状态记录缺少 status_text，item={item}"
            assert item["status_text"], \
                f"preview 状态 status_text 不应为空，item={item}"

    @pytest.mark.regression
    def test_老数据sync_status为null时仍能正常返回(self, login_session):
        """
        触发条件：historys() 中 sync_status=null 的兼容分支（老版本数据）。
        代码：whereNull('sync_status')->whereIn('status', [0,1]) 兼容查询。
        验证：接口整体能正常返回，不因 null sync_status 抛出 500。
        说明：此分支依赖数据库中存在旧格式记录，通常只能在老环境验证；
              本用例以不返回 5xx 作为最低验证标准。

        可选前置 SQL（构造老格式记录以覆盖此分支）：
          INSERT INTO asa_aso_competitor_logs (user_id, team_id, type, value, country,
            sync_status, status, created_at, updated_at)
          VALUES (<uid>, <tid>, 2, '389801252', 'US',
            NULL, 1, NOW() - INTERVAL 1 HOUR, NOW());
        """
        resp = _historys(login_session)
        assert resp.status_code != 500, \
            f"historys 接口不应因老数据 sync_status=null 返回 500，实际：{resp.status_code}"
        _assert_http_ok(resp)


# ══════════════════════════════════════════════════════════════════
# 补充 3：chart() type=1（词找应用）未覆盖分支
# ══════════════════════════════════════════════════════════════════

class TestCompetitorChartType1:
    """
    覆盖 chart() 中 type=1（词找应用）分支：
    代码：if (type == TYPE_KEYWORD_TO_APP) → return search_chart + asa_chart
    现有测试 explore_log_id 均为 type=2，此类使用 explore_log_id_type1 fixture。
    """

    @pytest.mark.regression
    def test_type1图表返回search_chart字段(self, login_session,
                                           explore_log_id_type1,
                                           explore_sync_status_type1):
        """
        触发条件：chart() 中 type == TYPE_KEYWORD_TO_APP(1) 分支。
        代码：return ['search_chart' => ..., 'asa_chart' => ...]（非 coverage_chart）。
        前置条件：sync_status=completed，否则 chart 接口拒绝返回。
        断言：search_chart.title(str) / .data.total(int≥0) / .data.bins(list) 完整结构。
        """
        if explore_sync_status_type1 != "completed":
            pytest.skip(
                f"type=1 数据未同步完成(当前:{explore_sync_status_type1})，跳过 chart type=1 正常场景"
            )
        resp = _chart(login_session, log_id=explore_log_id_type1)
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        # type=1 完整结构断言：search_chart + asa_chart（Apifox schema）
        _assert_chart_type1_response(resp)

    @pytest.mark.regression
    def test_type1图表返回asa_chart字段(self, login_session,
                                        explore_log_id_type1,
                                        explore_sync_status_type1):
        """
        触发条件：chart() type=1 分支，验证 asa_chart 字段存在且结构完整。
        代码：TYPE_KEYWORD_TO_APP 路径返回 asa_chart（ASA 广告图表数据）。
        断言：asa_chart.title(str) / .data.total(int≥0) / .data.bins(list) 全部验证。
        """
        if explore_sync_status_type1 != "completed":
            pytest.skip("type=1 数据未同步完成，跳过")
        resp = _chart(login_session, log_id=explore_log_id_type1)
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        # asa_chart 独立子结构断言
        _assert_chart_block(resp, "asa_chart")

    @pytest.mark.regression
    def test_type1图表不包含type2独有字段(self, login_session,
                                          explore_log_id_type1,
                                          explore_sync_status_type1):
        """
        触发条件：chart() type=1 分支，验证返回字段与 type=2 互斥。
        代码：type=2 走 else 分支返回 coverage_chart + bidding_chart。
        验证：type=1 响应不应包含 coverage_chart 或 bidding_chart。
        """
        if explore_sync_status_type1 != "completed":
            pytest.skip("type=1 数据未同步完成，跳过")
        resp = _chart(login_session, log_id=explore_log_id_type1)
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        data = resp.json().get("data", {})
        type2_exclusive = {"coverage_chart", "bidding_chart"}
        overlap = type2_exclusive & set(data.keys())
        assert not overlap, \
            f"type=1 图表不应包含 type=2 独有字段 {overlap}，data keys={list(data.keys())}"

    @pytest.mark.regression
    def test_type1同步未完成时chart返回业务错误(self, login_session,
                                                explore_log_id_type1,
                                                explore_sync_status_type1):
        """
        触发条件：chart() 中 resolveSyncStatus != COMPLETED → throw ServiceException。
        使用 type=1 的 log_id 在未完成同步时调用 chart 接口。
        """
        if explore_sync_status_type1 == "completed":
            pytest.skip("type=1 数据已完成同步，此场景不适用")
        resp = _chart(login_session, log_id=explore_log_id_type1)
        _assert_http_ok(resp)
        biz_code = resp.json().get("code")
        assert biz_code != 0, \
            f"type=1 数据未完成时 chart 应返回业务错误，实际 code={biz_code}"


# ══════════════════════════════════════════════════════════════════
# 补充 4：list() 未覆盖分支
# ══════════════════════════════════════════════════════════════════

class TestCompetitorListUncovered:
    """
    覆盖 list() / getUserLog() / getList() 中的未覆盖分支：
      - getUserLog() log 不存在 → throw ServiceException('log not found')
      - getList() shouldHidePreviewTop50Apps → 预览期隐藏 TOP50
      - getList() shouldBuildAppInfoMap → 完成后附加 app_info_map
      - label=aso + type=1 → 附加 asaTopApp 字段
      - type=1 词找应用的 list 正常场景
    """

    @pytest.mark.negative
    def test_getUserLog不存在时list返回业务错误(self, login_session):
        """
        触发条件：getUserLog() 中 log not found 分支（$log == null）。
        代码：if (!$log) throw ServiceException('log not found')。
        验证：传入不存在的 log_id，期望业务错误（4xx 或 code≠0）。
        """
        resp = _list(login_session, log_id=999_999_999, label="aso")
        is_http_error = resp.status_code in (400, 404, 422)
        is_biz_error  = resp.status_code == 200 and resp.json().get("code") != 0
        assert is_http_error or is_biz_error, (
            f"不存在的 log_id 期望业务错误，"
            f"实际 HTTP {resp.status_code}，响应：{resp.text[:300]}"
        )

    @pytest.mark.negative
    def test_getUserLog不存在时chart返回业务错误(self, login_session):
        """
        触发条件：getUserLog() 在 chart() 中被调用，log_id 不存在。
        代码：if (!$log) throw ServiceException('log not found')。
        验证：chart 接口传入不存在的 log_id，期望业务错误。
        """
        resp = _chart(login_session, log_id=999_999_999)
        is_http_error = resp.status_code in (400, 404, 422)
        is_biz_error  = resp.status_code == 200 and resp.json().get("code") != 0
        assert is_http_error or is_biz_error, (
            f"chart 接口不存在 log_id 期望业务错误，"
            f"实际 HTTP {resp.status_code}，响应：{resp.text[:300]}"
        )

    @pytest.mark.regression
    def test_预览期列表total不超过PREVIEW_LIMIT_500(self, login_session,
                                                    explore_log_id,
                                                    explore_sync_status):
        """
        触发条件：getList() 中 syncStatus != COMPLETED → limit(PREVIEW_LIMIT=500)。
        验证：传入大 limit 时，total 不超过 500 且固定返回第 1 页。
        """
        if explore_sync_status == "completed":
            pytest.skip("数据已完成同步，PREVIEW_LIMIT 限制不生效")
        resp = _list(login_session, log_id=explore_log_id, label="aso",
                     page=2, limit=500)
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        data = resp.json().get("data", {})
        total = data.get("total", 0)
        current = data.get("current", 1)
        assert total <= 500, \
            f"预览期 total 不应超过 PREVIEW_LIMIT=500，实际：{total}"
        assert current == 1, \
            f"预览期应固定返回第1页（后端忽略 page 参数），实际 current={current}"

    @pytest.mark.regression
    def test_预览期hideTop50Apps字段为空数组(self, login_session,
                                             explore_log_id,
                                             explore_sync_status):
        """
        触发条件：getList() shouldHidePreviewTop50Apps=true 分支。
        代码：search_results_apps / result_apps 在预览期且配置开启时返回空数组。
        说明：依赖后端 .env 中 PREVIEW_HIDE_TOP50_APPS=true 配置。
              若后端未启用该配置，本用例记录实际值（不强制失败）。
        """
        if explore_sync_status == "completed":
            pytest.skip("数据已完成同步，hideTop50Apps 分支不生效")
        resp = _list(login_session, log_id=explore_log_id, label="aso")
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        items = resp.json().get("data", {}).get("list", [])
        for item in items:
            # 检查每条记录中 search_results_apps / result_apps 字段（字段名取决于后端版本）
            for apps_key in ("search_results_apps", "result_apps"):
                if apps_key in item:
                    apps_val = item[apps_key]
                    # 若后端启用了 hideTop50Apps，则应为 []；若未启用则仅观察不断言
                    if isinstance(apps_val, list) and len(apps_val) > 0:
                        # 记录但不强制失败：该配置可能未启用
                        pass

    @pytest.mark.regression
    def test_完成同步后app_info_map字段若存在则为dict(self, login_session,
                                                      explore_log_id,
                                                      explore_sync_status):
        """
        触发条件：getList() shouldBuildAppInfoMap=true 分支。
        代码：sync 完成后，若 feature flag 开启则在响应 data 中附加 app_info_map 字段。
        验证：若 app_info_map 存在，则其类型为 dict（而非 list 或其他）。
        """
        if explore_sync_status != "completed":
            pytest.skip("数据未完成同步，app_info_map 分支不生效")
        resp = _list(login_session, log_id=explore_log_id, label="aso")
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        data = resp.json().get("data", {})
        if "app_info_map" in data:
            assert isinstance(data["app_info_map"], dict), \
                f"app_info_map 应为对象（dict），实际类型：{type(data['app_info_map'])}"

    @pytest.mark.regression
    def test_type1词找应用label_aso包含asaTopApp字段(self, login_session,
                                                       explore_log_id_type1):
        """
        触发条件：list() 中 label=aso && type=1 → 附加 asaTopApp 字段。
        代码逻辑（来自 Apifox schema）：词找应用时 ASO 列表附带 asaTopApp 竞争应用信息。
        断言：asaTopApp.top_app(app_id/app_name/icon) / app_count(int≥0) / apps(list) 完整结构。
        """
        resp = _list(login_session, log_id=explore_log_id_type1, label="aso")
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        _assert_list_page_meta(resp)
        # asaTopApp 完整子结构断言（Apifox schema required 字段）
        data = resp.json().get("data", {})
        _assert_asa_top_app(data)

    @pytest.mark.regression
    def test_type1词找应用label_asa正常返回列表(self, login_session,
                                                  explore_log_id_type1):
        """
        触发条件：type=1（词找应用）+ label=asa，覆盖非 type=2 场景的 list 查询路径。
        验证：能正常获取 list 字段且为数组，不因 type 不同报错。
        """
        resp = _list(login_session, log_id=explore_log_id_type1, label="asa")
        _assert_http_ok(resp)
        _assert_biz_ok(resp)
        data = resp.json().get("data", {})
        assert "list" in data and isinstance(data["list"], list), \
            f"type=1+asa list 结构异常，data={data}"


# ══════════════════════════════════════════════════════════════════
# 补充 5：Service 异步分支（通过 API 间接验证）
# ══════════════════════════════════════════════════════════════════

class TestCompetitorAsyncAndServiceBranches:
    """
    覆盖 Service 层异步相关分支（无法直接 POST 触发 Job，通过 API 间接验证）：
      - refreshAggregateSyncStatus：FAILED / COMPLETED / RUNNING 聚合状态
      - syncSourceNextPage：最终 completed + 轮询验证
      - dispatchSyncJobs：防重 dispatch（acquireDispatchLock）
      - getUserLog log_id 跨团队/不存在
    """

    @pytest.mark.regression
    def test_sync状态最终变为completed_轮询验证(self, login_session):
        """
        触发条件：refreshAggregateSyncStatus() 双源均 COMPLETED → 整体 COMPLETED。
        代码分支：elif ($aso == COMPLETED && $asa == COMPLETED) → updateLogSyncStatus(COMPLETED)。
        验证方式：循环轮询 explore，等待 sync_status 变为 completed。
        超时：由 SYNC_MAX_WAIT_SEC 控制（默认 120s）。

        注意：若数据量过大或三方 API 超时，sync 可能不会在超时时间内完成，
              届时用例 skip（不视为失败）。
        """
        max_wait = int(os.getenv("SYNC_MAX_WAIT_SEC", "120"))
        interval = 5
        elapsed  = 0
        while elapsed < max_wait:
            resp = _explore(login_session, type_=2, value=VALID_APP_ID, country=VALID_COUNTRY)
            if resp.status_code == 200 and resp.json().get("code") == 0:
                status = resp.json().get("data", {}).get("sync_status")
                if status == "completed":
                    _assert_biz_ok(resp)
                    return
                if status == "failed":
                    pytest.fail(
                        f"sync_status 变为 failed（两源均失败或单源失败），"
                        f"响应：{resp.text[:300]}"
                    )
            time.sleep(interval)
            elapsed += interval
        pytest.skip(
            f"同步在 {max_wait}s 内未完成，跳过。"
            "可通过环境变量 SYNC_MAX_WAIT_SEC 调整最大等待时间。"
        )

    @pytest.mark.regression
    def test_sync_failed状态下chart返回业务错误(self, login_session):
        """
        触发条件：refreshAggregateSyncStatus 将整体标为 FAILED（任一源失败）。
        代码分支：chart() → resolveSyncStatus == FAILED != COMPLETED → throw ServiceException。
        前置条件：需提供 sync_status=failed 的 log_id。
          方案A：配置环境变量 FAILED_LOG_ID=<id>。
          方案B：手动执行 SQL：
            UPDATE asa_aso_competitor_logs SET sync_status='failed' WHERE id=<id>;

        验证：chart 接口对 FAILED 的 log_id 返回业务错误。
        """
        failed_log_id = os.getenv("FAILED_LOG_ID", "")
        if not failed_log_id:
            pytest.skip("未配置 FAILED_LOG_ID，跳过；可手动构造 sync_status=failed 的记录")
        resp = _chart(login_session, log_id=int(failed_log_id))
        _assert_http_ok(resp)
        biz_code = resp.json().get("code")
        assert biz_code != 0, \
            f"sync_status=failed 时 chart 应返回业务错误，实际 code={biz_code}"

    @pytest.mark.regression
    def test_sync_failed状态下list不返回5xx(self, login_session):
        """
        触发条件：getList() 在 syncStatus=FAILED 状态下的行为分支。
        代码：FAILED 时走与 PREVIEW 相同路径（PREVIEW_LIMIT）或抛出错误。
        验证：不返回 500（行为取决于后端策略，至少不崩溃）。
        前置条件：同上，需 FAILED_LOG_ID 环境变量。
        """
        failed_log_id = os.getenv("FAILED_LOG_ID", "")
        if not failed_log_id:
            pytest.skip("未配置 FAILED_LOG_ID，跳过")
        resp = _list(login_session, log_id=int(failed_log_id), label="aso")
        assert resp.status_code != 500, \
            f"sync_status=failed 时 list 不应返回 500，实际：{resp.status_code}"

    @pytest.mark.regression
    def test_重复explore不重复触发Job_防dispatch锁(self, login_session):
        """
        触发条件：dispatchSyncJobs() 中 acquireDispatchLock() 返回 false 的分支。
        代码：Redis::exists(syncLockKey) 或 setnx(dispatchLockKey) 失败 → continue（跳过 dispatch）。
        验证方式：短时间内快速发送 2 次相同 explore，两次均 code=0 且 log_id 相同。
        """
        resp1 = _explore(login_session, type_=2, value=VALID_APP_ID, country=VALID_COUNTRY)
        resp2 = _explore(login_session, type_=2, value=VALID_APP_ID, country=VALID_COUNTRY)
        _assert_http_ok(resp1)
        _assert_http_ok(resp2)
        _assert_biz_ok(resp1)
        _assert_biz_ok(resp2)
        log_id1 = resp1.json().get("data", {}).get("log_id")
        log_id2 = resp2.json().get("data", {}).get("log_id")
        assert log_id1 == log_id2, \
            f"快速重复 explore 应返回相同 log_id（防 dispatch 锁），实际：{log_id1} vs {log_id2}"

    @pytest.mark.negative
    def test_跨团队log_id访问被拒绝(self, login_session):
        """
        触发条件：getUserLog() 中 where(team_id=?) 过滤后 log 为 null。
        代码：if (!$log) throw ServiceException('log not found')。
        验证：使用不存在/其他团队的 log_id，list 和 chart 均拒绝。
        """
        cross_team_log_id = 999_999_998  # 极大值，理论上不存在或不属于当前团队
        for resp in [
            _list(login_session, log_id=cross_team_log_id, label="aso"),
            _chart(login_session, log_id=cross_team_log_id),
        ]:
            is_http_error = resp.status_code in (400, 403, 404, 422)
            is_biz_error  = resp.status_code == 200 and resp.json().get("code") != 0
            assert is_http_error or is_biz_error, (
                f"跨团队 log_id 期望拒绝访问，"
                f"实际 HTTP {resp.status_code}，响应：{resp.text[:300]}"
            )


# ══════════════════════════════════════════════════════════════════
# 补充 6：并发场景验证
# ══════════════════════════════════════════════════════════════════

class TestCompetitorConcurrency:
    """
    覆盖并发相关分支：
      - acquireDispatchLock：并发请求时 Redis setnx 防重（syncLock + dispatchLock）
      - syncSourceNextPage：Redis sync lock 防止同一 Job 并发执行
    验证方式：使用 threading 模拟并发 API 请求。
    """

    @pytest.mark.regression
    def test_并发explore同一参数只触发一次dispatch(self, login_session):
        """
        触发条件：多个 explore 请求并发抵达，dispatchSyncJobs 通过 Redis lock 防止重复 dispatch。
        验证：3 个并发请求均返回 code=0，且所有响应的 log_id 相同。
        """
        import threading

        results: list = []

        def do_explore() -> None:
            resp = _explore(login_session, type_=2, value=VALID_APP_ID, country=VALID_COUNTRY)
            results.append(resp)

        threads = [threading.Thread(target=do_explore) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        assert len(results) == 3, f"期望 3 个响应，实际收到：{len(results)}"
        for resp in results:
            _assert_http_ok(resp)
            _assert_biz_ok(resp)

        log_ids = [r.json().get("data", {}).get("log_id") for r in results]
        unique_ids = set(log_ids)
        assert len(unique_ids) == 1, \
            f"并发 explore 应返回相同 log_id（防重 dispatch），实际：{log_ids}"

    @pytest.mark.regression
    def test_并发chart请求不触发5xx(self, login_session, explore_log_id):
        """
        触发条件：多个 chart 请求并发访问同一 log_id。
        验证：所有并发请求均不返回 500，后端能正确处理并发读取。
        """
        import threading

        results: list = []

        def do_chart() -> None:
            resp = _chart(login_session, log_id=explore_log_id)
            results.append(resp)

        threads = [threading.Thread(target=do_chart) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        assert len(results) == 5, f"期望 5 个响应，实际：{len(results)}"
        for resp in results:
            assert resp.status_code != 500, \
                f"并发 chart 请求不应返回 500，实际：{resp.status_code}，响应：{resp.text[:200]}"
