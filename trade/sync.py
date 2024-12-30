import time
import hashlib
import json
import math
import requests
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Order, Shop, Cart
from gallery.models import SKU  # 避免循环导入
from logistics.models import Package, Service  # 添加Package导入

# 获取logger实例
logger = logging.getLogger(__name__)

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

def get_trade_detail(trade_id):
    """获取订单明细数据"""
    body = {
        "tradeIds": [str(trade_id)]
    }
    body_str = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
    params, headers = generate_sign(body_str)
    
    url = "https://openapi.qizhishangke.com/api/openservices/trade/v1/getSalesTradeOrderList"
    response = requests.post(url, params=params, headers=headers, data=body_str)

    # 打印返回的数据结构
    # print("API返回数据:", response.json()['data'] )


    if response.status_code != 200:
        raise Exception(f"API请求失败: {response.text}")
        
    response_data = response.json()
    if response_data['code'] != 200:
        raise Exception(f"API返回错误: {response_data['message']}")
    

    
    return response_data['data']

def sync_trade_detail(order, trade_id):
    """同步订单商品明细"""
    try:
        # 获取订单明细数据
        details = get_trade_detail(trade_id)
        
        # 删除原有的购物车记录
        Cart.objects.filter(order=order).delete()
        
        # 同步商品明细
        for item in details:
            try:
                # 使用正确的字段名获取SKU编码
                sku_code = item.get('skuNo')
                if not sku_code:
                    logger.error(f"找不到SKU编码字段, 订单号: {order.order_no}, 数据: {item}")
                    continue
                    
                sku = SKU.objects.get(sku_code=sku_code)
                
                # 创建购物车记录
                Cart.objects.create(
                    order=order,
                    sku=sku,
                    qty=int(item.get('num', 1)),
                    price=float(item.get('price', 0)),
                    cost=float(item.get('cost', 0)),
                    discount=float(item.get('discount', 0)),
                    actual_price=float(item.get('actualPrice', item.get('price', 0))),
                    is_out_of_stock=False
                )
            except SKU.DoesNotExist:
                logger.error(f"找不到SKU: {sku_code}, 订单号: {order.order_no}")
                continue
            except Exception as e:
                logger.error(f"处理订单商品明细时出错: {str(e)}, 订单号: {order.order_no}")
                continue
                
    except Exception as e:
        logger.error(f"获取订单明细数据失败: {str(e)}, 订单号: {order.order_no}")

def sync_package_info(order, trade_data):
    """同步包裹信息"""
    logger.info(f"开始同步包裹信息, 订单号: {order.order_no}")
    logger.info(f"物流数据: {json.dumps(trade_data, ensure_ascii=False)}")
    
    try:
        # 检查物流信息
        logger.info(f"订单状态: {trade_data.get('tradeStatusDesc')}")
        logger.info(f"物流单号: {trade_data.get('logisticsNo')}")
        logger.info(f"物流公司代码: {trade_data.get('logisticsCompanyCode')}")
        
        # 获取物流服务，使用ID为1的默认服务
        try:
            service = Service.objects.get(id=1)
            logger.info(f"使用默认物流服务: {service}")
        except Service.DoesNotExist:
            logger.error("找不到默认物流服务(ID=1)")
            return
        except Exception as e:
            logger.error(f"获取物流服务时出错: {str(e)}")
            return

        # 创建或更新包裹记录
        try:
            package_data = {
                'order': order,
                'tracking_no': trade_data.get('logisticsNo', ''),  # 未发货时可能没有物流单号
                'pkg_status_code': '1' if trade_data.get('tradeStatusDesc') == '已发货' else '0',
                'service': service,
                'items': [],  # 商品信息暂时为空列表
                'shipping_fee': float(trade_data.get('postFee', 0))
            }
            logger.info(f"准备创建/更新包裹记录: {json.dumps(package_data, ensure_ascii=False, default=str)}")
            
            # 尝试获取现有包裹
            try:
                package = Package.objects.get(order=order)
                # 更新现有包裹
                for key, value in package_data.items():
                    setattr(package, key, value)
                package.save()
                logger.info(f"更新包裹记录成功: {package.tracking_no or '未获取跟踪号'}, 订单号: {order.order_no}")
            except Package.DoesNotExist:
                # 创建新包裹
                package = Package.objects.create(**package_data)
                logger.info(f"创建新包裹记录成功: {package.tracking_no or '未获取跟踪号'}, 订单号: {order.order_no}")
                
        except Exception as e:
            logger.error(f"创建/更新包裹记录时出错: {str(e)}")
            logger.error("错误详情: ", exc_info=True)
            return
            
    except Exception as e:
        logger.error(f"同步包裹信息失败: {str(e)}, 订单号: {order.order_no}")
        logger.error("错误详情: ", exc_info=True)

def sync_trade_data(start_date, end_date, page=1):
    """同步订单数据"""
    body = {
        "createTimeBegin": start_date,
        "createTimeEnd": end_date,
        "tradeStatusCode": 0,
        "pageNo": page,
        "pageSize": 100
    }
    body_str = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
    params, headers = generate_sign(body_str)
    
    url = "https://openapi.qizhishangke.com/api/openservices/trade/v1/getSalesTradeList"
    response = requests.post(url, params=params, headers=headers, data=body_str)
    
    if response.status_code != 200:
        raise Exception(f"API请求失败: {response.text}")
        
    response_data = response.json()
    if response_data['code'] != 200:
        raise Exception(f"API返回错误: {response_data['message']}")
        
    data = response_data['data']
    
    for item in data['data']:
        # 处理时间字段
        created_time = datetime.strptime(item['tradeTime'], "%Y-%m-%dT%H:%M:%S")
        try:
            shiped_time = datetime.strptime(item['deliveryTime'], "%Y-%m-%dT%H:%M:%S")
            shiped_date = shiped_time.date()
        except:
            shiped_time = None
            shiped_date = None
            
        try:
            operate_time = datetime.strptime(item['outBoundTime'], "%Y-%m-%dT%H:%M:%S")
        except:
            operate_time = None

        # 获取或创建Shop
        shop, _ = Shop.objects.get_or_create(
            code=item['shopNo'],
            defaults={
                'name': item['shopText'],
                'is_active': True
            }
        )

        # 状态映射
        status_mapping = {
            '待发货': Order.OrderStatus.PENDING,
            '已发货': Order.OrderStatus.SHIPPED,
            '已完成': Order.OrderStatus.COMPLETED,
            '已取消': Order.OrderStatus.CANCELLED,
            # 添加其他状态映射...
        }

        # 更新或创建Order
        order_data = {
            'platform_order_no': item['srcTids'],
            'order_no': item['tradeNo'],
            'recipient_country': item['country'],
            'recipient_state': item['receiverProvince'],
            'created_at': created_time,
            'shop': shop,
            'status': status_mapping.get(item['tradeStatusDesc'], Order.OrderStatus.PENDING),
            'paid_amount': float(item.get('payment', 0)),
            'freight': float(item.get('postFee', 0)),
            'recipient_name': item['receiverName'],
            'recipient_phone': item['receiverMobile'],
            'recipient_email': '',
            'recipient_city': item['receiverCity'],
            'recipient_address': item['receiverAddress'],
            'system_remark': item['erpRemark'],
            'cs_remark': item['csRemark'],
            'buyer_remark': item['buyerMessage']
        }

        try:
            # 创建或更新订单
            order, created = Order.objects.update_or_create(
                id=item['tradeId'],
                defaults=order_data
            )
            print('处理订单', item['srcTids'], '成功============================================================')
            
            # 同步订单商品明细
            sync_trade_detail(order, item['tradeId'])
            
            # 同步包裹信息
            sync_package_info(order, item)
            
        except Exception as e:
            logger.error(f"处理订单 {item['srcTids']} 时出错: {str(e)}")
            continue
    
    # 处理分页
    if page < math.ceil(data['total'] / data['pageSize']):
        sync_trade_data(start_date, end_date, page + 1)

def sync_all_trade():
    """同步所有订单数据"""
    try:
        # 设置同步的时间范围（比如最近7天的订单）
        end_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        
        # 开始同步数据
        sync_trade_data(start_date, end_date)
        
        return True, "订单数据同步成功"
    except Exception as e:
        logger.error(f"同步订单数据时出错: {str(e)}")
        return False, f"同步失败: {str(e)}" 