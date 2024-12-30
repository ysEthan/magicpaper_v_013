import time
import json
import hashlib
import requests
import math
import os
from datetime import datetime, timedelta
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from .models import SPU, SKU, Category

class ProductSync:
    def __init__(self):
        self.app_name = "mathmagic"
        self.app_key = "82be0592545283da00744b489f758f99"
        self.sid = "mathmagic"
        self.api_url = "https://openapi.qizhishangke.com/api/openservices/product/v1/getItemList"
        
    def generate_sign(self, body):
        headers = {
            'Content-Type': 'application/json'
        }

        timestamp = str(int(time.time()))
        sign_str = f"{self.app_key}appName{self.app_name}body{body}sid{self.sid}timestamp{timestamp}{self.app_key}"
        sign = hashlib.md5(sign_str.encode()).hexdigest()
        
        params = {
            "appName": self.app_name,
            "sid": self.sid,
            "sign": sign,
            "timestamp": timestamp,
        }
        return params, headers

    def sync_products(self, start_time=None, end_time=None, page=1):
        """同步产品数据"""
        print(f"开始同步第 {page} 页数据...")  # 添加调试信息
        
        if not start_time:
            # 默认同步最近7天的数据
            start_time = (datetime.now() - timedelta(days=85)).strftime('%Y-%m-%d %H:%M:%S')
        if not end_time:
            end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        print(f"同步时间范围: {start_time} 到 {end_time}")  # 添加调试信息

        body = {
            "page_size": 100,
            "page_no": page,
            "start_time": start_time,
            "end_time": end_time,
            "status": 0
        }

        body_str = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
        params, headers = self.generate_sign(body_str)

        try:
            response = requests.post(self.api_url, params=params, headers=headers, data=body_str)
            print(f"API响应状态码: {response.status_code}")  # 添加调试信息
            
            if response.status_code != 200:
                print(f"API响应内容: {response.text}")  # 添加调试信息
                raise Exception(f"API请求失败: {response.text}")

            result = response.json()
            if result['code'] != 200:
                raise Exception(f"业务处理失败: {result['message']}")

            data = result['data']
            total = data['total']
            page_size = data['pageSize']
            current_page = data['currentPage']
            max_page = math.ceil(total / page_size)

            # 处理当前页的数据
            synced_count = self._process_products(data['data'])

            # 如果还有下一页，递归处理
            if current_page < max_page :
                time.sleep(1)  # 避免请求过快
                next_count = self.sync_products(start_time, end_time, page + 1)
                synced_count += next_count

            return synced_count

        except Exception as e:
            print(f"发生异常: {str(e)}")  # 添加调试信息
            raise

    def _download_image(self, image_url, sku_code):
        """下载图片"""
        try:
            print(f"开始下载图片: {image_url}")
            
            # 添加请求头，模拟浏览器行为
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(image_url, headers=headers, timeout=30)
            if response.status_code == 200:
                # 检查内容类型
                content_type = response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    print(f"非图片内容类型: {content_type}")
                    return None
                    
                # 生成文件名
                ext = image_url.split('.')[-1].lower()
                if ext not in ['jpg', 'jpeg', 'png', 'gif']:
                    ext = 'jpg'
                filename = f"skus/{sku_code}.{ext}"  # 确保这个路径与 MEDIA_ROOT 相对应
                
                try:
                    # 删除旧图片
                    storage = default_storage
                    if storage.exists(filename):
                        storage.delete(filename)
                    
                    # 保存新图片
                    path = default_storage.save(filename, ContentFile(response.content))
                    print(f"图片保存成功: {path}")
                    return path
                except Exception as e:
                    print(f"保存图片失败: {str(e)}")
                    return None
            else:
                print(f"下载图片失败: HTTP {response.status_code}")
                print(f"响应内容: {response.text[:200]}")  # 只打印前200个字符
                return None
            
        except requests.exceptions.Timeout:
            print(f"下载图片超时: {image_url}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"请求图片失败: {str(e)}")
            return None
        except Exception as e:
            print(f"下载图片异常: {str(e)}")
            return None

    def _process_products(self, products):
        """处理产品数据"""
        synced_count = 0
        
        # 获取默认类目
        default_category = Category.objects.filter(is_last_level=True).first()
        if not default_category:
            raise Exception("系统中没有可用的最后一级类目，请先创建类目")
        
        for product in products:
            try:
                print(f"开始处理产品: {product['specNo']}")
                
                # 根据 className 查找对应的类目
                category = default_category  # 默认类目
                if product.get('className'):
                    try:
                        # 将中文类目名转换为英文格式（去除空格，转小写）
                        class_name_en = product['className'].replace(' ', '').lower()
                        # 尝试通过英文名称匹配类目
                        category = Category.objects.filter(
                            category_name_en__iexact=class_name_en,  # 不区分大小写匹配
                        ).first() or default_category
                        
                        if category == default_category:
                            print(f"未找到类目 {product['className']}({class_name_en})，使用默认类目")
                    except Category.DoesNotExist:
                        print(f"未找到类目 {product['className']}，使用默认类目")
                
                # 处理SPU
                spu_defaults = {
                    'spu_name': product['goodsName'],
                    'status': True,
                    'category': category,  # 使用匹配到的类目
                }
                
                try:
                    spu = SPU.objects.get(spu_code=product['goodsNo'])
                    # 如果 SPU 已存在，不更新类目
                    spu_defaults['category'] = spu.category
                except SPU.DoesNotExist:
                    pass
                
                spu, created = SPU.objects.update_or_create(
                    spu_code=product['goodsNo'],
                    defaults=spu_defaults
                )
                print(f"SPU {'创建' if created else '更新'} 成功: {spu.spu_code}")

                # 处理SKU
                sku_defaults = {
                    'sku_name': product['specName'],
                    'plating_process': product['prop4'] or 'none',  # 电镀工艺，如果为空则为'none'
                    'color': product['prop2'] or '无',  # 颜色
                    'material': product['prop8'] or '无',  # 材质
                    'length': float(product['length']) if product['length'] else 0,
                    'width': float(product['width']) if product['width'] else 0,
                    'height': float(product['height']) if product['height'] else 0,
                    'weight': float(product['weight']) if product['weight'] else 0,
                    'status': True,
                    'spu': spu,
                    # 将供应商信息存储在suppliers_list中
                    'suppliers_list': json.dumps([{
                        'code': p['providerNo'],
                        'name': p['providerName']
                    } for p in product['providerList']]) if product['providerList'] else '[]'
                }

                # 处理图片
                if product.get('imgUrl'):
                    image_url = product['imgUrl']
                    print(f"发现图片URL: {image_url}")
                    # 移除时间戳参数
                    image_url = image_url.split('?')[0]
                    image_path = self._download_image(image_url, product['specNo'])
                    if image_path:
                        sku_defaults['img_url'] = image_path

                sku, created = SKU.objects.update_or_create(
                    sku_code=product['specNo'],
                    defaults=sku_defaults
                )
                print(f"SKU {'创建' if created else '更新'} 成功: {sku.sku_code}")
                
                synced_count += 1

            except Exception as e:
                print(f"处理产品数据失败: {str(e)}, 产品: {product['specNo']}")
                print(f"错误详情: {type(e).__name__}")
                print(f"产品数据: {product}")
                continue

        return synced_count

    def clean_old_images(self, days=30):
        """清理指定天数之前的旧图片"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            storage = default_storage
            directory = 'skus/'
            
            # 获取目录中的所有文件
            _, files = storage.listdir(directory)
            
            for filename in files:
                try:
                    path = os.path.join(directory, filename)
                    # 获取文件的修改时间
                    modified_time = datetime.fromtimestamp(storage.get_modified_time(path).timestamp())
                    
                    # 如果文件超过指定天数且不是当前使用的图片，则删除
                    if modified_time < cutoff_date:
                        # 检查是否有SKU正在使用这个图片
                        if not SKU.objects.filter(img_url=path).exists():
                            storage.delete(path)
                            print(f"删除旧图片: {path}")
                            
                except Exception as e:
                    print(f"处理文件时出错 {filename}: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"清理旧图片时出错: {str(e)}") 