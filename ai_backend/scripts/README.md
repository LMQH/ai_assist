# 服务管理脚本说明

## server.sh

后端服务管理脚本，用于启动、停止、重启和管理后端服务。

## 使用方法

```bash
./scripts/server.sh <命令> [选项]
```

## 命令列表

### start [端口号]
启动服务

- 如果不指定端口号，从 `config.json` 读取配置
- 如果指定端口号，会自动更新配置文件
- 服务在后台运行

示例：
```bash
./scripts/server.sh start          # 使用配置文件中的端口
./scripts/server.sh start 8003     # 在8003端口启动并更新配置
```

### stop [端口号]
停止服务

示例：
```bash
./scripts/server.sh stop           # 停止配置文件中的端口服务
./scripts/server.sh stop 8003      # 停止8003端口的服务
```

### restart [端口号]
重启服务

示例：
```bash
./scripts/server.sh restart        # 重启服务
```

### status [端口号]
查看服务状态

- 显示服务是否运行
- 显示进程ID
- 执行健康检查

示例：
```bash
./scripts/server.sh status         # 查看服务状态
```

### config <端口号>
更新配置端口号

- 更新 `config.json` 中的端口配置

示例：
```bash
./scripts/server.sh config 8003    # 更新端口为8003
```

### logs
查看实时日志

- 使用 `tail -f` 显示日志文件内容
- 按 Ctrl+C 退出

示例：
```bash
./scripts/server.sh logs           # 查看实时日志
```

### help
显示帮助信息

示例：
```bash
./scripts/server.sh help
```

## 注意事项

1. **conda环境**: 脚本需要conda环境，默认环境名为 `cs-assist-ai`
2. **端口占用**: 启动前会自动检查端口是否被占用，如果被占用会尝试停止现有服务
3. **环境变量**: 启动前会检查 `.env` 文件是否存在
4. **日志文件**: 日志保存在 `nohup.out` 文件中

## 配置文件

脚本使用的配置文件：
- `config.json` - 服务配置（端口等）

## 日志文件

- `nohup.out` - 服务运行日志

