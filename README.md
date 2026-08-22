# free_deepseek     
通过逆向deepseek网页模型调用逻辑将网页模型换为api     
     




# 安装     
需要使用微信扫码登录deepseek网页账号     
     
完整安装命令     
```bash
git clone https://github.com/CuteeCat/free_deepseek.git
cd free_deepseek
g++ -O3 -fopenmp pow.cpp -o pow.exe
pip install playwright
playwright install
pip install requests
python login.py
python main.py -p "你好"
```

# 原理     
     
逆向网页api调用协议，期中对话接口需要算法工作量证明，这里使用c++协助完成，结果拼接在请求头    
免费的deepseekapi，喵喵喵~~~，就是模型不咋地
