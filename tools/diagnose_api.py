import urllib.request
import json

print("=" * 70)
print("诊断 API 调用问题")
print("=" * 70)

endpoints = [
    ("健康检查", "http://localhost:8080/api/health"),
    ("统计数据", "http://localhost:8080/api/admin/stats"),
    ("动作标准", "http://localhost:8080/api/pose/standards")
]

for name, url in endpoints:
    try:
        print(f"\n✓ 测试 {name}")
        print(f"  URL: {url}")
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/json')
        req.add_header('Origin', 'http://localhost:3000')
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            print(f"  ✓ 响应成功 (状态码: {response.status})")
            print(f"  返回数据类型: {type(data).__name__}")
            if isinstance(data, dict):
                print(f"  字段: {list(data.keys())}")
            elif isinstance(data, list) and len(data) > 0:
                print(f"  数组大小: {len(data)}")
                print(f"  第一项字段: {list(data[0].keys())}")
    except Exception as e:
        print(f"  ✗ 错误: {e}")

print("\n" + "=" * 70)
print("\n现在测试浏览器 CORS 预检请求...")
print("=" * 70)

try:
    import http.client
    conn = http.client.HTTPConnection("localhost", 8080)
    conn.request("OPTIONS", "/api/admin/stats", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET"
    })
    res = conn.getresponse()
    print(f"\nOPTIONS 预检响应:")
    print(f"  状态码: {res.status}")
    headers = res.getheaders()
    for key, val in headers:
        if "access-control" in key.lower():
            print(f"  {key}: {val}")
    conn.close()
except Exception as e:
    print(f"  ✗ 错误: {e}")
