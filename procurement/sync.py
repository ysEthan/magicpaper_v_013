import time
import hashlib
import json
import math
import requests
from datetime import datetime, timedelta
from django.utils import timezone
from .models import PurchaseOrder, PurchaseOrderDetail, Supplier
from gallery.models import SKU
from storage.models import Warehouse

def generate_sign(body):
    """生成API签名"""
    appName = "mathmagic"
    appKey = "82be0592545283da00744b489f758f99"
    sid = "mathmagic"

    headers = {
        'Content-Type': 'application/json'
    }

    timestamp = str(int(time.time()))
    sign_str = "{appKey}appName{appName}body{body}sid{sid}timestamp{timestamp}{appKey}".format(
        appKey=appKey, appName=appName, body=body, sid=sid, timestamp=timestamp
    )
    sign = hashlib.md5(sign_str.encode()).hexdigest()
    
    params = {
        "appName": appName,
        "sid": sid,
        "sign": sign,
        "timestamp": timestamp,
    }
    return params, headers

def sync_purchase_data(start_date, end_date, page=1):
    """同步采购单数据"""
    success_count = 0
    error_count = 0
    
    # 准备请求数据
    body = {
        "pageSize": 200,
        "pageNo": page,
        "createTimeBegin": start_date,
        "createTimeEnd": end_date,
        "orderStatus": [40, 42, 75, 70, 10],  # 待下单 待支付 待入库 已完成 已作废
        "account": "admin"
    }
    
    body_str = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
    params, headers = generate_sign(body_str)
    
    # 发送API请求
    url = "https://openapi.qizhishangke.com/api/openservices/purchaseOrder/v1/getOrders"
    response = requests.post(url, params=params, headers=headers, data=body_str.encode('utf-8'))
    
    if response.status_code != 200:
        raise Exception(f"API请求失败: {response.text}")
        
    response_data = response.json()
    if response_data.get('code') != 200:
        raise Exception(f"API返回错误: {response_data.get('message')}")
        
    data = response_data.get('data', {})
    items = data.get('data', [])
    if not items:
        return success_count, error_count

    # 状态映射
    status_mapping = {
        '待下单': PurchaseOrder.Status.PENDING_ORDER,
        '待支付': PurchaseOrder.Status.PENDING_PAYMENT,
        '待入库': PurchaseOrder.Status.PENDING_STORAGE,
        '已完成': PurchaseOrder.Status.STORED,
        '已作废': PurchaseOrder.Status.CANCELLED,
        '草稿': PurchaseOrder.Status.DRAFT,
    }
    
    item_count = 0
    # 处理每条采购单数据
    for item in items:
        item_count += 1
        print("处理第"+str(item_count)+"条采购单:"+item['purchaseNo']+":"+item['status'])
        try:
            # 检查必要字段
            required_fields = ['purchaseNo', 'status', 'created', 'providerName', 'specNo']
            if not all(field in item for field in required_fields):
                error_count += 1
                continue
            print("必要字段存在")
            # 获取状态
            status = status_mapping.get(item['status'])
            if not status or status == PurchaseOrder.Status.DRAFT:
                print("状态不存在")
                continue
            print("状态存在")
            # 处理时间
            created_time = datetime.strptime(item['created'], "%Y-%m-%d %H:%M:%S")
            trade_time = datetime.strptime(item['tradeTime'], "%Y-%m-%d %H:%M:%S") if item.get('tradeTime') else None

            # 处理供应商
            supplier, _ = Supplier.objects.get_or_create(
                name=item['providerName'],
                defaults={'contact_info': ''}
            )
            print("供应商存在")

            # 处理仓库
            warehouse = None
            warehouse_id = item.get('warehouseId')
            if warehouse_id:
                warehouse = Warehouse.objects.filter(id=warehouse_id).first()
                print(f"仓库ID: {warehouse_id}, 找到仓库: {warehouse.name if warehouse else 'None'}")

            # 处理价格和数量
            price_str = ''.join(c for c in item.get('price', '') if c.isdigit() or c == '.')
            total_amount = float(price_str) if price_str else 0

            quantity_str = ''.join(c for c in str(item.get('num', '0')) if c.isdigit() or c == '.')
            quantity = float(quantity_str) if quantity_str else 0

            print("采购单号:"+item['purchaseNo']+", 供应商:"+item['providerName']+", 数量:"+str(quantity)+", 金额:"+str(total_amount))  
            print("创建采购单")

            # 创建采购单
            purchase_order_data = {
                'purchase_order_number': item['purchaseNo'],
                'supplier': supplier,
                'warehouse': warehouse,
                'purchase_date': created_time.date(),
                'status': status,
                'expected_delivery_date': trade_time.date() if trade_time else created_time.date(),
                'total_amount': total_amount,
                'created_at': created_time,
                'updated_at': timezone.now()
            }

            purchase_order, _ = PurchaseOrder.objects.update_or_create(
                purchase_order_number=item['purchaseNo'],
                defaults=purchase_order_data
            )

            # 创建采购单明细
            sku = SKU.objects.get(sku_code=item['specNo'])
            detail_data = {
                'purchase_order': purchase_order,
                'product': sku,
                'quantity': quantity,
                'unit_price': total_amount / quantity if quantity > 0 else 0,
                'amount': total_amount
            }

            PurchaseOrderDetail.objects.update_or_create(
                purchase_order=purchase_order,
                product=sku,
                defaults=detail_data
            )
            success_count += 1
            
        except Exception as e:
            print(f"处理采购单时出错: {str(e)}")
            error_count += 1
            continue
    
    # 处理分页
    total = data.get('total', 0)
    pageSize = data.get('pageSize', 200)
    currentPage = data.get('currentPage', 1)
    max_page = math.ceil(total / pageSize)
    
    if max_page > currentPage:
        next_success, next_error = sync_purchase_data(start_date, end_date, currentPage + 1)
        success_count += next_success
        error_count += next_error
    
    return success_count, error_count

def sync_all_purchase():
    """同步所有采购单数据"""
    try:
        end_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        start_date = (datetime.now() - timedelta(days=9)).strftime("%Y-%m-%d %H:%M:%S")
        
        success_count, error_count = sync_purchase_data(start_date, end_date)
        return True, f"采购单同步完成，成功: {success_count} 条，失败: {error_count} 条"
    except Exception as e:
        return False, f"同步采购单时发生错误: {str(e)}" 