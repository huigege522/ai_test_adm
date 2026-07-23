# -*- coding: utf-8 -*-
"""
基本信息管理 · 测试点清单中暂不自动化场景的 pytest.skip 占位。

便于在报告中追溯编号（季度任务 / OAuth / 待确认需求等）。
"""

from __future__ import annotations

import pytest


class TestBlockedQuarterlyAndOAuth:
    @pytest.mark.skip(reason="TC039：季度第6周媒体清单对齐依赖定时任务与环境配置")
    def test_TC039(self):
        raise AssertionError("unreachable")

    @pytest.mark.skip(
        reason=(
            "TC040：OAuth 全流程需浏览器授权与三方回调；"
            "写库逻辑见 apple_cmp_api/tests/Feature/Asa/OrgManagementServiceUpsertFromOAuthTest.php"
        )
    )
    def test_TC040(self):
        raise AssertionError("unreachable")

    @pytest.mark.skip(reason="TC008/TC208：企查查接口依赖三方可用性或 Mock")
    def test_TC008_TC208_qichacha(self):
        raise AssertionError("unreachable")

    @pytest.mark.skip(reason="TC056–TC058：新客标识自动流转策略依赖脚本与清单下发")
    def test_TC056_TC058_net_new_auto(self):
        raise AssertionError("unreachable")

    @pytest.mark.skip(reason="TC313–TC319：新客状态机长周期与时序依赖数据库时钟/季度任务")
    def test_TC313_TC319_state_machine(self):
        raise AssertionError("unreachable")


class TestBlockedRelationEditPendingConfirm:
    @pytest.mark.skip(reason="TC035：关系编辑需求「待确认」，文档章节已移除")
    def test_TC035(self):
        raise AssertionError("unreachable")

    @pytest.mark.skip(reason="TC223：关系编辑重复校验逻辑待产品确认")
    def test_TC223(self):
        raise AssertionError("unreachable")

    @pytest.mark.skip(reason="TC235/TC332：关系管理编辑入口是否保留待确认")
    def test_TC235_TC332(self):
        raise AssertionError("unreachable")


class TestBlockedSecurityExpectations:
    @pytest.mark.skip(reason="TC239：绕过 UI 直接改全新客的接口鉴权策略需安全评审后断言")
    def test_TC239(self):
        raise AssertionError("unreachable")

    @pytest.mark.skip(reason="TC238：监控「无人工变为全新客」需日志/定时审计链路")
    def test_TC238(self):
        raise AssertionError("unreachable")


class TestBlockedFrontendTc053Tc054:
    @pytest.mark.skip(
        reason=(
            "TC053/TC054：前端 ProductDialog.vue 仍含「负责人」「客户结算」等区块；"
            "待与 apple_cmp_web 对齐需求后再启用 UI/E2E 断言"
        )
    )
    def test_TC053_TC054_product_dialog_layout(self):
        raise AssertionError("unreachable")
