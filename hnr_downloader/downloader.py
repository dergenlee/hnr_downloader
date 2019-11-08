
import os
import time
import datetime
import requests
import traceback
import threading
from urllib.parse import unquote, urlparse

from hnr_downloader import helper

STARTING = _('准备下载')
RETRY = _('正在第 {} 次重试')
DOWNLOADING = _('正在下载')
FAILED = _('下载失败')
NOT_START = _('未开始')
COMPLETED = _('已下载')
PAUSED = _('下载暂停')
INFO_RETRIEVED = _('已获取信息')
ERROR = _('错误: {}')

lock = threading.Lock()
locka=  threading.Lock()

def get_filename_from_url(url):
    fn = os.path.basename(urlparse(url).path).lower() or 'index.html'
    f, ext = os.path.splitext(fn)
    if not ext:
        fn = f'{fn}.html'
    return fn


def get_ext_of_content_encoding(encoding):
    return f'.{encoding}' if encoding else ''


class CannotStopDownloadException(Exception):
    def __init__(self,message=None):
        message=message or _('不能停止下载')
        super().__init__(message)

class Download():
    def __init__(self, url=None, save_to=None, dict=None, config=None):
        self.url = url
        self.save_to = save_to
        self.config = config
        self.http_proxy = None
        self.https_proxy = None

        self.clear()
        if dict:
            for key in dict.keys():
                if hasattr(self, key):
                    setattr(self, key, dict[key])

    def get_proxies(self):
        if self.http_proxy == '':
            self.http_proxy = None
        if self.https_proxy == '':
            self.https_proxy = None

        return {
            'http': self.http_proxy,
            'https': self.https_proxy or self.http_proxy
        }

    def to_dict(self):
        res = {
            'url': self.url,
            'http_proxy': self.http_proxy,
            'https_proxy': self.https_proxy,
            'resumable': self.resumable,
            'save_to': self.save_to,
            'filename': self.filename,
            'size': self.size,
            'content-type': self.content_type,
            'status': self.status,
            'is_paused': self.is_paused,
            'has_completed': self.has_completed,
        }
        if self.has_completed:
            res.update({
                'downloaded_file': self.downloaded_file,
                'current_speed': self.current_speed,
                'consumed_time': self.consumed_time})
        else:
            res.update({'tmppath': self.tmppath})

        return res

    def clear(self):
        self.save_to = None
        self.filename = None
        self.size = 0
        self.current_speed = 0
        self.downloaded = 0
        self.start_time = None
        self.consumed_time = None
        self.remain_time = None
        self.downloaded_file = None
        self.thread = None
        self.headers = None
        self.tmppath = None
        self.downloading = False
        self.status = NOT_START
        self.last_error = ''
        self.content_type = None
        self.has_completed = False
        self.is_paused = False
        self.resumable = True

        self.stop = False

    @property
    def percent(self):
        strsize = helper.strsize(self.size)
        strdownloaded = helper.strsize(self.downloaded)
        per = f'{self.downloaded/self.size:0.0%}' if self.size > 0 else '-'
        if self.has_completed:
            return f'{strsize}(100%)'
        else:
            return f'{strdownloaded}({per})/{strsize}'

    def fetch_file_info(self, url, **kwargs):
        self.clear()
        self.url = url
        resume_header = {
            'Range': 'bytes=0-'}
        try:
            resp = requests.head(
                url,
                proxies=self.get_proxies(),
                headers=resume_header,
                allow_redirects=True,
                **kwargs)
        except requests.exceptions.MissingSchema as e:
            self.status = ERROR.format(_('链接地址格式不对'))
            self.last_error = str(e)
            if self.config.debug:
                traceback.print_exc()
        except requests.exceptions.ConnectionError as e:
            self.status = ERROR.format(_('不能连接到 {}').format(url))
            self.last_error = str(e)
            if self.config.debug:
                traceback.print_exc()
        except Exception as e:
            self.status = ERROR.format(str(e))
            self.last_error = str(e)
            if self.config.debug:
                traceback.print_exc()
        else:
            if resp.ok:
                self.headers = {
                    key.lower(): value
                    for key, value in resp.headers.items()}

                content_dispostion = self.headers.get(
                    'content-disposition', None)
                content_encoding = self.headers.get(
                    'content-encoding', None)
                content_size = self.headers.get('content-length', None)

                accept_ranges = self.headers.get('accept-ranges', '').lower()
                self.resumable = accept_ranges == 'bytes'

                try:
                    self.size = int(content_size)
                except Exception:
                    self.size = 0

                if content_dispostion:
                    fn = unquote(content_dispostion.split(';', 1)[1])
                    self.filename = fn.split('=', 1)[1]
                else:
                    self.filename = unquote(
                        get_filename_from_url(url) +
                        get_ext_of_content_encoding(content_encoding))

                self.filename = helper.sanitize(self.filename)

                self.content_type = self.headers.get('content-type', None)

                self.status = INFO_RETRIEVED
            else:
                self.handleStatusCode(resp.status_code)

    def start_download(self):
        if not os.path.exists(self.save_to):
            os.makedirs(self.save_to)

        self.get_tmppath()
        self.thread = threading.Thread(target=self.do_download)

        self.start_time = datetime.datetime.now()

        self.status = STARTING
        self.thread.start()

    def do_download(self):
        if self.downloading:
            return

        retry = 0
        has_error = False

        download_from = self.downloaded
        with open(self.tmppath, 'ab') as f:
            self.set_downloading(True)
            while not self.size or self.downloaded < self.size:
                if self.stop:
                    break

                if self.resumable:
                    resume_header = {
                        'Range': f'bytes={self.downloaded}-'}
                else:
                    resume_header = {}
                    self.downloaded = 0
                    f.truncate(0)
                try:
                    resp = requests.get(
                        self.url,
                        stream=True,
                        proxies=self.get_proxies(),
                        headers=resume_header)
                    if resp.ok:
                        self.status = RETRY.format(
                            retry) if retry else DOWNLOADING
                        prev_time = datetime.datetime.now()
                        prev_downloaded = self.downloaded

                        self.headers = {
                            key.lower(): value
                            for key, value in resp.headers.items()}
                        self.content_type = self.headers.get(
                            'content-type', None)

                        r = resp.raw
                        while True:
                            chunk = r.read(64 * 1024)
                            if not chunk:
                                break

                            f.write(chunk)
                            self.downloaded += len(chunk)
                            this_time = datetime.datetime.now()
                            secs = (this_time - prev_time).total_seconds()
                            if secs >= 1:
                                this_downloaded = self.downloaded - prev_downloaded
                                prev_time = this_time
                                
                                prev_downloaded = self.downloaded
                                self.current_speed = int(
                                    this_downloaded / secs)
                                if self.current_speed and self.size > 0:
                                    self.remain_time = (
                                        self.size - self.downloaded) / self.current_speed
                                else:
                                    self.remain_time = None

                                self.consumed_time = (
                                    this_time - self.start_time).total_seconds()

                                if self.stop:
                                    break

                                if secs > 60:   # 1分钟保存一次
                                    f.flush()

                    else:
                        self.handleStatusCode(resp.status_code)
                        has_error = True
                        break

                    if self.size == 0:
                        break

                except Exception as e:
                    retry += 1
                    self.last_error = str(e)
                    if self.config.debug:
                        traceback.print_exc()

                    if retry >= self.config.max_retry:
                        self.status = FAILED
                        has_error=True
                        break
        if not has_error:
            if not self.stop:
                if self.downloaded >= self.size:
                    self.downloaded_file = helper.find_suitable_filename(
                        self.tmppath[0:-5])

                    os.rename(self.tmppath, self.downloaded_file)

                    self.status = COMPLETED
                    self.has_completed = True
                    self.consumed_time = (
                        datetime.datetime.now() - self.start_time).total_seconds()
                    self.current_speed = (
                        self.downloaded - download_from) / self.consumed_time
                    self.remain_time = 0

                else:
                    self.status = FAILED
            else:
                self.status = PAUSED
                self.is_paused = True

        self.set_downloading(False)

    def set_downloading(self,downloading=True):
        locka.acquire()
        self.downloading=downloading
        if downloading:
            self.stop = False 
        locka.release()

    def set_stop(self, stopped=True):
        lock.acquire()
        self.stop = stopped
        lock.release()

    def stop_download(self, wait_for_stopped=True, timeout=60):
        self.set_stop()

        end_time = datetime.datetime.now() + datetime.timedelta(seconds=timeout)
        if wait_for_stopped:
            while self.downloading:
                time.sleep(0.5)
                if datetime.datetime.now() > end_time:
                    return False
        return True

    def destroy(self, delete_downloaded_file=False):
        stopped = self.stop_download()
        if not stopped:
            raise CannotStopDownloadException()

        if self.tmppath and os.path.exists(self.tmppath):
            try:
                os.remove(self.tmppath)
            except Exception as e:
                self.last_error = str(e)
                if self.config.debug:
                    traceback.print_exc()

        if delete_downloaded_file and os.path.exists(self.downloaded_file):
            try:
                os.remove(self.downloaded_file)
            except Exception as e:
                self.last_error = str(e)
                if self.config.debug:
                    traceback.print_exc()

    def handleStatusCode(self, status_code):
        if status_code == 302:
            self.status = ERROR.format(_('需要登录'))
        elif status_code == 404:
            self.status = ERROR.format(_('找不到文件'))
        else:
            self.status = ERROR.format(_('返回错误代码：{}').format(status_code))

        self.last_error = _('返回错误代码：{}').format(status_code)

        if self.config.debug:
            print(self.last_error)

    def get_tmppath(self):
        if self.filename:
            tmpfile = self.filename + ".part"
            self.tmppath = os.path.join(self.save_to, tmpfile)

            self.downloaded = 0
            if os.path.exists(self.tmppath):
                self.downloaded = os.path.getsize(self.tmppath)
