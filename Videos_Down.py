import os
from concurrent.futures import ThreadPoolExecutor
import subprocess
import time
import sys

# 关机函数【调用windows内置shutdown.exe命令关机】
def shutdown_system():
    """    关闭系统    """
    print("⏳ 准备关机...")
    try:
        if os.name == 'nt':  # Windows系统
            os.system("shutdown /s /t 60")  # 60秒后关机
            print("💻 Windows系统将在30秒后关机，按Ctrl+C取消")
        else:  # Unix/Linux/Mac系统
            os.system("shutdown -h +1")  # 1分钟后关机
            print("💻 Unix/Linux/Mac系统将在1分钟后关机，按Ctrl+C取消")
    except Exception as e:
        print(f"❌ 关机命令执行失败: {e}")

# 取消关机函数
def cancel_shutdown():
    """    取消关机    """
    try:
        if os.name == 'nt':  # Windows系统
            os.system("shutdown /a")
        else:  # Unix/Linux/Mac系统
            os.system("shutdown -c")
        print("🛑 已取消关机")
    except Exception as e:
        print(f"❌ 取消关机失败: {e}")

# 设置环境变量以确保 Python 的标准输入输出使用 UTF-8 编码。
env = os.environ.copy()
env['PYTHONIOENCODING'] = 'utf-8'

"""
os.environ.copy()
复制当前系统的环境变量，创建一个新的字典 env。
这样可以在不影响原始环境变量的情况下进行修改。
env['PYTHONIOENCODING'] = 'utf-8'
设置环境变量 PYTHONIOENCODING 为 'utf-8'。
该环境变量用于指定 Python 进程的标准输入、输出和错误流的编码方式。
在某些系统或终端环境下，可能会出现编码问题（例如中文乱码），通过显式设置为 UTF-8 可以避免此类问题。
"""

# 下载单个M3U8视频
def download_single_m3u8(url, output_filename, use_ffmpeg=True, resume=True, shutdown=False, transcode=True):
    """
    下载单个M3U8视频（支持断点续传）

    Args:
        url: M3U8视频链接
        output_filename: 输出文件名
        use_ffmpeg: 是否使用FFmpeg下载
        resume: 是否启用断点续传
        shutdown: 下载完成后是否自动关机

    Returns:
        bool: 下载是否成功
    """
    # 确保输出文件名有正确的扩展名
    if not output_filename.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
        output_filename += '.mp4'

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)    # 创建输出目录,若目录已存在，则忽略，不会报错，默认为：False

    # 检查是否存在部分下载的文件，支持断点续传
    if resume and os.path.exists(output_filename):
        print(f"检测到未完成的下载文件: {output_filename}，FFmpeg将覆盖此文件...")

    if transcode:  # use_ffmpeg
        command = [
            'ffmpeg',
            '-i', url,
            '-c', 'copy',
            # '-c:a', 'aac',
            # '-crf', '23',
            # '-pix_fmt', 'yuv4200p',
            '-bsf:a', 'aac_adtstoasc',
            '-rw_timeout', '30000000',  # 读写超时30秒
            '-reconnect', '1',  # 启用重连
            '-reconnect_at_eof', '1',  # EOF时重连
            '-reconnect_streamed', '1',  # 流媒体重连
        ]

        # 添加-y参数以允许覆盖已存在的文件
        if resume:
            command.extend(['-y', output_filename])
        else:
            command.append(output_filename)

        print(f"执行命令: {' '.join(command)}")
        print(f"开始下载: {output_filename}")

        try:
            # 实时输出，不捕获输出内容
            process = subprocess.Popen(command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            env=env)

            start_time = time.time()
            last_progress_time = start_time

            # 实时显示输出
            while True:
                output = process.stdout.readline()
                if output == b'' and process.poll() is not None:
                    break
                if output:
                    try:
                        print(output.decode('utf-8', errors='ignore').strip())
                    except UnicodeDecodeError:
                        # 如果解码失败，尝试使用 gb18030 编码
                        try:
                            print(output.decode('gb18030', errors='ignore').strip())
                        except:
                            print(output.strip())

                    # 每隔一定时间显示一次进度更新
                    current_time = time.time()
                    if current_time - last_progress_time > 30:  # 每30秒显示一次进度
                        elapsed = current_time - start_time
                        print(
                            f"[进度更新] 已用时: {int(elapsed // 60)}分{int(elapsed % 60)}秒, 正在处理: {output_filename}")
                        last_progress_time = current_time

            rc = process.poll()
            end_time = time.time()
            duration = end_time - start_time

            if rc == 0:
                file_size = os.path.getsize(output_filename) if os.path.exists(output_filename) else 0
                size_mb = file_size / (1024 * 1024)
                print(f"✅ 下载完成: {output_filename}")
                print(f"   文件大小: {size_mb:.2f} MB")
                print(f"   耗时: {int(duration // 60)}分{int(duration % 60)}秒")

                # 如果设置了自动关机，则执行关机
                if shutdown:
                    shutdown_system()
                return True
            else:
                print(f"❌ 下载失败 {output_filename}")
                print(f"   耗时: {int(duration // 60)}分{int(duration % 60)}秒")
                # 下载失败时取消关机（如果之前设置了）
                if shutdown:
                    print("⚠️  下载失败，取消自动关机")
                    cancel_shutdown()
                return False

        except FileNotFoundError:
            print("❌ 错误: 未找到ffmpeg，请先安装ffmpeg")
            if shutdown:
                print("⚠️  由于ffmpeg未找到，取消自动关机")
                cancel_shutdown()
            return False
        except KeyboardInterrupt:
            print("\n⚠️  用户中断下载，取消自动关机")
            cancel_shutdown()
            sys.exit(1)
        except Exception as e:
            print(f"❌ 下载过程中发生错误 {output_filename}: {e}")
            if shutdown:
                print("⚠️  下载出错，取消自动关机")
                cancel_shutdown()
            return False

# 单个下载示例（下载完成后自动关机）
# download_single_m3u8(狙击精英_战纪, r'E:\Videos\zhj.mp4', resume=True, shutdown=True)


def batch_download_m3u8(video_list, output_dir="E:\\Download", resume=True, shutdown=False):
    """
    批量下载M3U8视频（支持断点续传）

    Args:
        video_list: [(url, filename), ...] 视频列表
        output_dir: 输出目录
        resume: 是否启用断点续传
        shutdown: 下载完成后是否自动关机
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 准备下载任务
    tasks = []
    for url, filename in video_list:
        # 确保文件名有正确的扩展名
        if not filename.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
            filename += '.mp4'
        output_path = os.path.join(output_dir, filename)
        tasks.append((url, output_path))

    # 并发下载
    print(f"开始批量下载 {len(tasks)} 个视频...")
    start_time = time.time()

    try:
        with ThreadPoolExecutor(max_workers=3) as executor:  # 限制并发数避免被封
            futures = [executor.submit(download_single_m3u8, url, path, True, resume) for url, path in tasks]

            success_count = 0
            for i, future in enumerate(futures):
                print(f"\n[任务进度] 正在处理第 {i + 1}/{len(tasks)} 个视频...")
                if future.result():
                    success_count += 1
                print(f"[任务完成] 总体进度: {i + 1}/{len(tasks)}, 成功: {success_count}")

        end_time = time.time()
        total_duration = end_time - start_time

        print(f"\n批量下载完成!")
        print(f"成功: {success_count}/{len(tasks)}")
        print(f"总耗时: {int(total_duration // 60)}分{int(total_duration % 60)}秒")

        # 如果设置了自动关机且下载成功，则执行关机
        if shutdown and success_count > 0:
            shutdown_system()
        elif shutdown and success_count == 0:
            print("⚠️  没有下载成功，取消自动关机")

    except KeyboardInterrupt:
        print("\n⚠️  用户中断下载，取消自动关机")
        cancel_shutdown()
        sys.exit(1)


# 使用示例：
# 1. 单个下载完成后关机
# download_single_m3u8(r"https://v4.ppqrrs.com/wjv4/202603/31/jM3YVq68vZ94/video/1000k_720/hls/index.m3u8", 'E:\\Videos\\video_.mp4', resume=True, shutdown=True)

# 2. 批量下载完成后关机
# video_list = [(urls_dict[i],f"琅琊榜之风起长林_{i}.mp4") for i in range(20,51)]
# video_list = [(urls_dict[i], f"ymewd_{i}.mp4") for i in range(ip.start_num, ip.end_num + 1)]

# 视频列表
video_list = [

    ('https://v10.baofeng10.com/video/miyuji/246fa1460b1b/index.m3u8', '蜜语纪_31.mp4'),

]

video_listB=[

    ("https://v2.ppqrrs.com/wjv2/202605/15/rn6w83BQ6986/video/1000k_720/hls/index.m3u8", "致命撞击_青春情杀案.mp4")

]

# batch_download_m3u8(video_list, "D:\\Videos", resume=True, shutdown=True)
# batch_download_m3u8(video_list, output_dir="E:\\Videos\\电视剧\\密语纪", shutdown=True)
# batch_download_m3u8(video_listB, output_dir="E:\\Videos\\电影", shutdown=True)