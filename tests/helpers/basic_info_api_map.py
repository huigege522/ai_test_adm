# -*- coding: utf-8 -*-
"""
基本信息管理 · OpenAPI / Laravel 路由对照（V3.24.0.0.0）

源：`apple_cmp_api/docs/V3.24.0.0.0 基本信息管理-Apifox.openapi.yaml`

TC→接口（P0 摘要，便于追溯测试点编号）：
  TC001/TC005/TC003/TC004/TC060 → POST /api/org/list（筛选 bloc_search / company_search / org_id / org_name）
  TC011/TC210 → POST /api/org/verifyOrgId
  TC008/TC208 → POST /api/org/checkCompany（企查查 · 自动化建议 Mock / 手工）
  TC007/TC011/TC017/TC212/TC213/TC201–TC207 → POST /api/org/verifyOrgId · add · edit
  TC041/TC042/TC044 → POST /api/app/list（org_name / customer_attribute 聚合展示）
  TC019/TC023/TC024/TC026/TC214–TC220 → POST /api/app/list · verifyAdamId · add · edit
  TC031/TC033/TC034/TC036/TC222/TC240/TC310 → POST /api/apple-relation/list · add · delete
  TC033 → org/list + app/list|verifyAdamId（关系弹窗名称带出）
  TC401–TC408 → 集成：org/add → app/add → apple-relation/add；TC403 产品主链路（见 integration）

说明：
  - 测试点 TC024/TC217 要求「客户属性非必填」；当前 Laravel `AppManagementController::add`
    仍为 `customer_attribute` required（与 OpenAPI AppAddRequest 一致）。对应断言按**后端现状**编写，
    并在用例 docstring 中标明与 PDF 的差异。
"""

PATH_ORG_LIST = "/api/org/list"
PATH_ORG_VERIFY = "/api/org/verifyOrgId"
PATH_ORG_CHECK_COMPANY = "/api/org/checkCompany"
PATH_ORG_ADD = "/api/org/add"
PATH_ORG_EDIT = "/api/org/edit"
PATH_ORG_FILTER_OPTIONS = "/api/org/filterOptions"
PATH_ORG_PARENT_ORG_LIST = "/api/org/parentOrgList"

PATH_APP_FILTER_OPTIONS = "/api/app/filterOptions"

PATH_APP_LIST = "/api/app/list"
PATH_APP_VERIFY_ADAM = "/api/app/verifyAdamId"
PATH_APP_ADD = "/api/app/add"
PATH_APP_EDIT = "/api/app/edit"
PATH_APP_BATCH_EDIT = "/api/app/batchEdit"

PATH_RELATION_LIST = "/api/apple-relation/list"
PATH_RELATION_ADD = "/api/apple-relation/add"
PATH_RELATION_DELETE = "/api/apple-relation/delete"
PATH_RELATION_FILTER_OPTIONS = "/api/apple-relation/filterOptions"

# 广告批量搭建 · 推广 APP 下拉（TC311 联动，权限 per:bulkSetup.view）
PATH_AD_GET_APP_SELECTOR = "/api/ad/getAppSelector"
