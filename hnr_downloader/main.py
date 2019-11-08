"""
恒睿下载：一个用Python实现的简单下载管理器

特点：
    断点续传
    记录下载任务状态
    下载任务单独指定代理服务器

要求的模块：
    wxPython>=4.0.7
    requests>=2.22.0

"""

import os
import time
import datetime
import json

import wx

from hnr_downloader import helper
from hnr_downloader.i18n import i18n
from hnr_downloader.add import AddDownloadDialog
from hnr_downloader.downloader import Download
from hnr_downloader.config import HnrConfig

appPath = os.path.abspath(os.path.dirname(__file__))


class MainPanel(wx.Panel):
    download_lists = None
    downloads = {}
    config = None

    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent

        self.config = HnrConfig(os.path.join(appPath, 'config.json'))

        self.downloads = self.get_log_downloads()

        self.add_btn = wx.Button(self, wx.ID_ANY, _('添加下载'))
        self.pause_btn = wx.Button(self, wx.ID_ANY, _('暂停下载'))
        self.start_btn = wx.Button(self, wx.ID_ANY, _('开始下载'))
        self.delete_btn = wx.Button(self, wx.ID_ANY, _('删除'))
        self.config_btn = wx.Button(self, wx.ID_ANY, _('配置'))
        self.exit_btn = wx.Button(self, wx.ID_ANY, _('退出'))

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        btn_sizer.Add(self.add_btn, 0, wx.ALL, 5)
        btn_sizer.Add(self.pause_btn, 0, wx.ALL, 5)
        btn_sizer.Add(self.start_btn, 0, wx.ALL, 5)
        btn_sizer.Add(self.delete_btn, 0, wx.ALL, 5)
        btn_sizer.Add(self.config_btn, 0, wx.ALL, 5)
        btn_sizer.Add(self.exit_btn, 0, wx.ALL, 5)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.download_lists = wx.ListCtrl(
            self, size=(-1, 200),
            style=wx.LC_REPORT | wx.BORDER_SUNKEN | wx.LC_VRULES | wx.LC_SINGLE_SEL)
        self.download_lists.InsertColumn(
            0, _('链接'), wx.LIST_FORMAT_LEFT, width=-1)
        self.download_lists.InsertColumn(
            1, _('文件名'), wx.LIST_FORMAT_LEFT, width=180)
        self.download_lists.InsertColumn(
            2, _('进度'), wx.LIST_FORMAT_CENTER, width=180)
        self.download_lists.InsertColumn(
            3, _('速度'), wx.LIST_FORMAT_CENTER, width=120)
        self.download_lists.InsertColumn(
            4, _('已用时间/剩余时间'), wx.LIST_FORMAT_CENTER, width=160)
        self.download_lists.InsertColumn(
            5, _('状态'), wx.LIST_FORMAT_CENTER, width=100)

        self.info_text = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.BORDER_SUNKEN | wx.TE_READONLY | wx.TE_RICH2,
            size=(-1, 200))

        main_sizer.Add(btn_sizer, 0, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(self.download_lists, 0, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(self.info_text, 0, wx.ALL | wx.EXPAND, 5)

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)

        self.add_dlg = AddDownloadDialog(self, _('添加下载'), self.config)

        # 绑定事件

        self.Bind(wx.EVT_SIZE, self.on_size, self)           # panel大小改变
        self.Bind(wx.EVT_BUTTON, self.on_add, self.add_btn)        # add_btn
        self.Bind(wx.EVT_BUTTON, self.on_config, self.config_btn)  # config_btn
        self.Bind(wx.EVT_BUTTON, self.on_exit, self.exit_btn)      # eixtBtn
        self.Bind(wx.EVT_BUTTON, self.on_start, self.start_btn)     # start_btn
        self.Bind(
            wx.EVT_BUTTON,
            self.on_delete,
            self.delete_btn)   # delete_btn
        self.Bind(wx.EVT_BUTTON, self.on_pause, self.pause_btn)     # pause_btn
        self.Bind(
            wx.EVT_LIST_ITEM_SELECTED,
            self.on_download_selected,
            self.download_lists)  # download_lists 选择
        self.Bind(
            wx.EVT_LIST_ITEM_DESELECTED,
            self.on_download_selected,
            self.download_lists)  # download_lists 选择

        self.Bind(
            wx.EVT_LIST_ITEM_ACTIVATED,
            self.on_open_downloaded_file,
            self.download_lists)  # download_lists 激活（双击或回车）

        self.init_menu()

        # 设定按钮初始状态
        self.disable_buttons()
        # 刷新下载列表
        self.refresh_download_lists()

    def init_menu(self):
        self.popup_menu = wx.Menu(_('恒睿下载'))
        self.open_menu_item = self.popup_menu.Append(wx.ID_ANY, _('打开文件'))
        self.folder_menu_item = self.popup_menu.Append(
            wx.ID_ANY, _('打开文件所在文件夹'))
        self.popup_menu.AppendSeparator()
        self.add_menu_item = self.popup_menu.Append(wx.ID_ANY, _('添加下载'))
        self.pause_menu_item = self.popup_menu.Append(wx.ID_ANY, _('暂停下载'))
        self.start_menu_item = self.popup_menu.Append(wx.ID_ANY, _('开始下载'))
        self.delete_menu_item = self.popup_menu.Append(wx.ID_ANY, _('删除'))

        self.Bind(wx.EVT_MENU, self.on_add, self.add_menu_item)
        self.Bind(wx.EVT_MENU, self.on_start, self.start_menu_item)
        self.Bind(wx.EVT_MENU, self.on_delete, self.delete_menu_item)

        self.Bind(
            wx.EVT_MENU,
            self.on_open_downloaded_file,
            self.open_menu_item)
        self.Bind(wx.EVT_MENU, self.on_open_folder, self.folder_menu_item)

        self.Bind(wx.EVT_CONTEXT_MENU, self.on_context, self.download_lists)

    def on_context(self, evt):
        self.PopupMenu(self.popup_menu)

    def on_open_folder(self, evt):
        index, download = self.get_selected_download()
        if download is None:
            return
        file = download.downloaded_file or download.tmppath

        if file is None:
            return

        path = os.path.dirname(file)

        if os.path.exists(path):
            os.startfile(path)

    def on_open_downloaded_file(self, evt):
        '''双击列表项或按回车'''
        #url = evt.GetItem().GetText()
        #download = self.downloads.get(url, None)

        index, download = self.get_selected_download()
        if download is None or not download.has_completed:
            return

        if not os.path.exists(download.downloaded_file or ''):
            return

        try:
            os.startfile(download.downloaded_file)
        except Exception as e:
            wx.MessageBox(
                _('发生错误：{e}').format(e=e),
                '恒睿下载',
                wx.OK | wx.ICON_ERROR,
                self)

    def on_start(self, evt):
        index, download = self.get_selected_download()
        if download:
            download.start_download()

            self.refresh_info_text(download)

            self.start_btn.Disable()
            self.pause_btn.Enable()

    def on_pause(self, evt):
        index, download = self.get_selected_download()
        if download:
            self.disable_buttons()
            download.stop_download(True)
            self.start_btn.Enable()
            self.delete_btn.Enable()

    def on_delete(self, evt):
        index, download = self.get_selected_download()
        if index < 0 or download is None:
            self.disable_buttons()
            return

        if wx.MessageBox(
                _("真的删除选定的下载吗？"),
                _("恒睿下载"),
                wx.YES_NO | wx.ICON_QUESTION,
                self) == wx.NO:
            return

        self.parent.timer.Stop()
        self.disable_buttons()

        delete_file = False
        if download.has_completed:
            delete_file = wx.MessageBox(
                _("同时删除已经下载的文件吗？"),
                _("恒睿下载"),
                wx.YES_NO | wx.ICON_QUESTION,
                self) == wx.YES

        download.destroy(delete_file)

        self.downloads.pop(download.url)

        self.download_lists.DeleteItem(index)

        self.parent.timer.Start()

    def on_download_selected(self, evt):
        download = self.set_buttons()
        self.refresh_info_text(download)

    def on_size(self, event):
        size = event.GetSize()
        dpos = self.info_text.GetPosition()

        width = size.GetWidth() - dpos.x * 2
        info_height = size.GetHeight() - dpos.y - 5
        self.download_lists.SetSize(width, -1)
        self.info_text.SetSize(width, info_height)

        width = self.download_lists.GetClientSize().GetWidth()
        itemCount = self.download_lists.GetColumnCount()
        for i in range(1, itemCount):
            width -= self.download_lists.GetColumnWidth(i)
        self.download_lists.SetColumnWidth(0, max(100, width))

    def on_add(self, event):
        self.add_dlg.clear()
        if self.add_dlg.ShowModal() == wx.ID_OK:
            d = self.add_dlg.download

            ed = self.downloads.get(d.url, None)
            if ed:
                if wx.MessageBox(
                    _("链接地址已经在下载列表，是否替换？"),
                    _("恒睿下载"),
                    wx.YES_NO | wx.ICON_QUESTION,
                        self) == wx.NO:
                    return
                if ed.downloading:
                    ed.stop_download(True)

            self.downloads.update({d.url: d})

            if self.config.auto_start:
                d.start_download()

            self.refresh_download_lists()

    def on_config(self, event):
        wx.MessageBox(_("已配置"), _("恒睿下载"), wx.OK | wx.ICON_INFORMATION)

    def on_exit(self, event):
        self.parent.Close()

    ############### 辅助函数 ###############

    def disable_buttons(self):
        self.start_btn.Disable()
        self.delete_btn.Disable()
        self.pause_btn.Disable()

        self.start_menu_item.Enable(False)
        self.delete_menu_item.Enable(False)
        self.pause_menu_item.Enable(False)
        self.open_menu_item.Enable(False)
        self.folder_menu_item.Enable(False)
        self.info_text.SetValue(_('...恒睿下载...'))

    def set_buttons(self):
        index, download = self.get_selected_download()
        if download:
            if download.downloading:
                self.pause_btn.Enable()
                self.start_btn.Disable()
            else:
                self.pause_btn.Disable()
                self.pause_menu_item.Enable(False)
                self.start_btn.Enable()
                self.start_menu_item.Enable()
                if download.is_paused:
                    self.start_btn.SetLabel(_('继续下载'))
                    self.start_menu_item.SetItemLabel(_('继续下载'))
                elif download.has_completed:
                    self.start_btn.SetLabel(_('重新下载'))
                    self.start_menu_item.SetItemLabel(_('重新下载'))
                else:
                    self.start_btn.SetLabel(_('开始下载'))
                    self.start_menu_item.SetItemLabel(_('开始下载'))
            self.delete_btn.Enable()
            self.delete_menu_item.Enable()

            file = download.downloaded_file or download.tmppath

            self.open_menu_item.Enable(file is not None)
            self.folder_menu_item.Enable(file is not None)
        else:
            self.disable_buttons()

        return download

    def cleanup(self):
        if any([download.downloading for download in self.downloads.values()]):
            if wx.MessageBox(
                _("还有任务在下载，是否真的退出？"),
                _("恒睿下载"),
                wx.YES_NO | wx.ICON_QUESTION,
                    self) == wx.NO:
                return False

        for download in self.downloads.values():
            download.stop_download()

        # 等待所有下载停止,超过2分钟则直接退出
        t = datetime.datetime.now()
        while any([download.downloading for download in self.downloads.values()]):
            time.sleep(0.5)
            if (datetime.datetime.now() - t).total_seconds() > 120:
                break

        d = [download.to_dict() for download in self.downloads.values()]

        logfile = os.path.join(appPath, 'log.json')

        data = {
            'save_time': helper.now_str(),
            'downloads': d, }

        with open(logfile, 'w', encoding='utf-8') as f:
            try:
                json.dump(data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                wx.MessageBox(_('不能保存下载记录：{e}').format(e=e))

        self.config.write_config()

        return True

    def refresh_download_lists(self):
        rindex = 0
        total_speed = 0
        total_downloadings = 0
        for download in self.downloads.values():
            if download.downloading:
                total_speed += download.current_speed
                total_downloadings += 1

            index = self.get_item(download.url)
            if index == wx.NOT_FOUND:
                index = self.download_lists.InsertItem(rindex, download.url)
                rindex += 1

            self.download_lists.SetItem(index, 1, download.filename or '')

            self.download_lists.SetItem(index, 2, download.percent)

            self.download_lists.SetItem(
                index, 3, f'{helper.strspeed(download.current_speed)}')

            s = f'{helper.strduration(download.consumed_time)}'
            if download.downloading:
                s += f'/{helper.strduration(download.remain_time)}'

            self.download_lists.SetItem(index, 4, s)
            self.download_lists.SetItem(index, 5, download.status or '')

        self.set_buttons()

        return total_downloadings, total_speed

    def refresh_info_text(self, download):
        if download is None:
            return

        info = ''
        info += _('链接地址: {}\n').format(download.url)
        info += _('代理地址（http）：{}\n').format(download.http_proxy)
        info += _('代理地址（https）：{}\n').format(download.https_proxy)
        info += _('断点续传: {}\n').format(_('是')
                                       if download.resumable else _('否'))
        info += _('文件名: {}\n').format(download.filename)
        info += _('文件大小：{}\n').format(helper.strsize(download.size, True))
        info += _('已下载: {}\n').format(helper.strsize(download.downloaded, True))
        info += _('保存位置: {}\n').format(download.save_to)
        if download.has_completed:
            info += _('已下载的文件: {}\n').format(download.downloaded_file)
            info += _('下载速度: {}\n').format(helper.strspeed(download.current_speed))
            info += _('下载耗时: {}\n').format(helper.strduration(download.consumed_time))

        if download.downloading:
            info += _('临时文件: {}\n').format(download.tmppath)
            info += _('开始时间：{}\n').format(helper.format_datetime(download.start_time))

        info += _('内容类型: {}\n').format(download.content_type)

        info += _('最后错误：{}\n\n').format(download.last_error)

        if download.headers:
            info += '___________________Headers________________________\n'
            for key, value in download.headers.items():
                info += f'{key}: {value}\n'

        self.info_text.SetValue(info)

    def get_item(self, text, col=0):
        for idx in range(self.download_lists.GetItemCount()):
            item = self.download_lists.GetItem(idx, col)
            if item.GetText() == text:
                return idx
        return wx.NOT_FOUND

    def get_selected_download(self):
        index = self.download_lists.GetFirstSelected()

        if index < 0:
            return index, None

        url = self.download_lists.GetItem(index).GetText()

        return index, self.downloads.get(url, None)

    def get_log_downloads(self):
        logfile = os.path.join(appPath, 'log.json')
        current_downloads = {}
        if os.path.exists(logfile):
            with open(logfile, 'r', encoding='utf-8') as f:
                try:
                    d = json.load(f)
                except BaseException:
                    pass
                else:
                    downloads = d.get('downloads', {})
                    for d in downloads:
                        download = Download(dict=d, config=self.config)
                        if not download.has_completed:
                            if self.config.auto_start:
                                download.start_download()
                            else:
                                download.get_tmppath()

                        current_downloads.update({download.url: download})

        return current_downloads


class MainForm(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(
            self,
            None,
            wx.ID_ANY,
            title=_('恒睿下载'),
            size=(1000, 600))

        self.panel = MainPanel(self)
        self.init_statusbar()
        self.init_timer()

        self.Bind(wx.EVT_CLOSE, self.on_close, self)

    def on_close(self, evt):
        self.timer.Stop()
        if self.panel.cleanup():
            evt.Skip()
        else:
            self.timer.Start()
            evt.Veto()

    def init_statusbar(self):
        self.CreateStatusBar(number=4)
        self.SetStatusWidths([-1, 200, 200, 120])
        self.SetStatusText(_("欢迎使用恒睿下载..."))
        self.SetStatusText(helper.now_str(), 3)

    def init_timer(self):
        self.timer = wx.Timer(self)
        self.timer.Start(1000)
        self.Bind(wx.EVT_TIMER, self.on_timer)

    def on_timer(self, event):
        self.SetStatusText(helper.now_str(), 3)
        dls, tspeed = self.panel.refresh_download_lists()
        if dls > 0:
            self.SetStatusText(_('正在下载任务数：{}').format(dls), 1)
            self.SetStatusText(
                _('下载总速度：{}').format(
                    helper.strspeed(tspeed)), 2)
        else:
            self.SetStatusText('', 1)
            self.SetStatusText('', 2)


def start():
    app = wx.App()
    frame = MainForm().Show()
    app.MainLoop()


if __name__ == '__main__':
    start()
