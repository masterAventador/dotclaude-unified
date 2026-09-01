# -*- coding: utf-8 -*-
"""ask_remote_rm.should_ask() 的单元测试:命令同时含整词 ssh 与 rm/rmdir 才要求人工审批。"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from ask_remote_rm import should_ask  # noqa: E402

ASK = [
    'ssh root@49.233.213.109 "rm -rf /srv/mosquitto/data"',
    'ssh root@49.233.213.109 "rm -f /tmp/x && echo DONE"',
    "ssh host rm file.txt",
    "ssh -o ConnectTimeout=5 user@host 'rmdir /data/old'",
    'cd /tmp && ssh host "rm -rf /x"',
    "echo rm -rf /x | ssh host bash",
    'ssh host "docker run --rm img"',       # 误弹可接受:宁多问不漏拦
    'ssh host "journalctl | grep rm"',      # 同上
]

PASS = [
    "rm -rf /tmp/local-file",               # 本地 rm:不归本钩子管
    "rmdir /tmp/empty",
    'ssh root@49.233.213.109 "tail -f /var/log/mosquitto/mosquitto.log"',
    "ssh host 'systemctl restart vpp-lights'",
    'ssh host "echo confirm && ls format"', # confirm/format 不含 rm 整词
    "npm rm some-package",                  # 有 rm 无 ssh
    "echo sshhh",                           # sshhh 不含 ssh 整词
    "git commit -m '整理 ssh 配置文档'",
    "ls -la",
]


def main():
    failed = 0
    for cmd in ASK:
        if not should_ask(cmd):
            print(f"FAIL 应审批却放过: {cmd}")
            failed += 1
    for cmd in PASS:
        if should_ask(cmd):
            print(f"FAIL 应放过却要审批: {cmd}")
            failed += 1
    total = len(ASK) + len(PASS)
    if failed:
        print(f"RESULT: FAILED {failed}/{total}")
        sys.exit(1)
    print(f"RESULT: PASSED {total}/{total}")


if __name__ == "__main__":
    main()
