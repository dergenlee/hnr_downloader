"""
A dialog for adding download tasks.
"""

import os

import wx

from hnr_downloader import helper
from hnr_downloader.downloader import Download


class AddDownloadDialog(wx.Dialog):

    def __init__(self, parent=None, title='', config=None, *args, **kwargs):
        super().__init__(parent, title=title, *args, **kwargs)

        self.ok = False

        self.config = config
        self.download = Download(config=self.config)

        url_label = wx.StaticText(
            self, label=_('链接地址'), style=wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE, size=(
                100, -1))
        self.url_text = wx.TextCtrl(self, size=(400, -1))
        self.retrieve_btn = wx.Button(self, label='→')
        url_sizer = wx.BoxSizer(wx.HORIZONTAL)
        url_sizer.Add(url_label, 0, wx.ALL, 5)
        url_sizer.Add(self.url_text, 0, wx.ALL, 5)
        url_sizer.Add(self.retrieve_btn, 0, wx.ALL, 5)

        self.retrieve_btn.Disable()

        file_label = wx.StaticText(self, label=_(
            '文件名称'), style=wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE, size=(100, -1))
        self.filename_text = wx.TextCtrl(self, size=(400, -1))
        file_sizer = wx.BoxSizer(wx.HORIZONTAL)
        file_sizer.Add(file_label, 0, wx.ALL, 5)
        file_sizer.Add(self.filename_text, 0, wx.ALL, 5)

        size_label = wx.StaticText(self, label=_(
            '文件大小'), style=wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE, size=(100, -1))
        self.size_text = wx.TextCtrl(
            self, style=wx.TE_READONLY, size=(400, -1))
        size_sizer = wx.BoxSizer(wx.HORIZONTAL)
        size_sizer.Add(size_label, 0, wx.ALL, 5)
        size_sizer.Add(self.size_text, 0, wx.ALL, 5)

        proxy_label = wx.StaticText(self, label=_(
            '代理地址'), style=wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE, size=(100, -1))
        self.proxy_http_text = wx.TextCtrl(self, size=(195, -1))
        self.proxy_https_text = wx.TextCtrl(self, size=(195, -1))
        proxy_sizer = wx.BoxSizer(wx.HORIZONTAL)
        proxy_sizer.Add(proxy_label, 0, wx.ALL, 5)
        proxy_sizer.Add(self.proxy_http_text, 0, wx.ALL, 5)
        proxy_sizer.Add(self.proxy_https_text, 0, wx.ALL, 5)

        self.Bind(wx.EVT_TEXT, self.on_url_change, self.url_text)
        self.Bind(wx.EVT_BUTTON, self.on_url, self.retrieve_btn)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_url, self.url_text)

        path_label = wx.StaticText(self, label=_(
            '保存路径'), style=wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE, size=(100, -1))
        self.path_text = wx.TextCtrl(
            self, size=(400, -1), style=wx.TE_READONLY)
        self.browse_btn = wx.Button(self, label=_('浏览'))

        path_sizer = wx.BoxSizer(wx.HORIZONTAL)
        path_sizer.Add(path_label, 0, wx.ALL, 5)
        path_sizer.Add(self.path_text, 0, wx.ALL, 5)
        path_sizer.Add(self.browse_btn, 0, wx.ALL, 5)

        dummy_label = wx.StaticText(
            self, label='', style=wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE, size=(
                100, -1))
        self.auto_start_check = wx.CheckBox(self, label=_('自动开始下载'))
        self.auto_change_default_save_to_check = wx.CheckBox(
            self, label=_('自动改变默认保存路径'))

        check_sizer = wx.BoxSizer(wx.HORIZONTAL)
        check_sizer.Add(dummy_label, 0, wx.ALL, 5)
        check_sizer.Add(self.auto_start_check, 0, wx.ALL, 5)
        check_sizer.Add(self.auto_change_default_save_to_check, 0, wx.ALL, 5)

        self.Bind(wx.EVT_BUTTON, self.on_browse, self.browse_btn)

        btn_sizer = self.CreateSeparatedButtonSizer(wx.OK | wx.CANCEL)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(url_sizer, 0, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(proxy_sizer, 0, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(file_sizer, 0, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(size_sizer, 0, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(path_sizer, 0, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(check_sizer, 0, wx.ALL | wx.EXPAND, 5)

        main_sizer.Add(btn_sizer, 0, wx.ALL | wx.EXPAND, 5)

        self.SetSizer(main_sizer)

        main_sizer.Fit(self)

        self.ok_btn = self.FindWindowById(wx.ID_OK)
        self.cancel_btn = self.FindWindowById(wx.ID_CANCEL)

        self.ok_btn.SetLabel(_('确定'))
        self.cancel_btn.SetLabel(_('取消'))

        # init control from config
        self.auto_start_check.SetValue(self.config.auto_start)
        self.auto_change_default_save_to_check.SetValue(
            self.config.auto_change_default_save_to)
        self.path_text.SetValue(self.config.default_save_to or os.getcwd())
        self.proxy_http_text.SetValue(self.config.last_used_http_proxy or '')
        self.proxy_https_text.SetValue(self.config.last_used_https_proxy or '')

        self.Bind(wx.EVT_BUTTON, self.on_ok, self.ok_btn)

        self.set_buttons()

    def set_buttons(self, enable=True):
        if enable:
            self.cancel_btn.Enable()
            self.browse_btn.Enable()
            self.filename_text.Enable()
        else:
            self.cancel_btn.Disable()
            self.browse_btn.Disable()
            self.filename_text.Disable()

        if enable and self.ok:
            self.ok_btn.Enable()
        else:
            self.ok_btn.Disable()

        if enable and helper.is_url(self.url_text.GetValue().strip()):
            self.retrieve_btn.Enable()
        else:
            self.retrieve_btn.Disable()

    def on_ok(self, event):
        filename = helper.sanitize(self.filename_text.GetValue())
        if not filename:
            wx.MessageDialog(self, _('请输入有效的文件名'), caption=_('恒睿下载'),
                             style=wx.OK | wx.CENTRE).ShowModal()
            return False
        if not self.ok:
            wx.MessageDialog(self, _('请输入有效的下载地址'), caption=_('恒睿下载'),
                             style=wx.OK | wx.CENTRE).ShowModal()
            return False

        self.download.http_proxy = self.proxy_http_text.GetValue()
        self.download.https_proxy = self.proxy_https_text.GetValue()
        self.download.save_to = self.path_text.GetValue() or os.getcwd()
        self.download.filename = filename

        if self.download.http_proxy:
            self.config.last_used_http_proxy = self.download.http_proxy
        if self.download.https_proxy:
            self.config.last_used_https_proxy = self.download.https_proxy
        self.config.auto_change_default_save_to = self.auto_change_default_save_to_check.GetValue()
        self.config.auto_start = self.auto_start_check.GetValue()
        if self.config.auto_change_default_save_to:
            self.config.default_save_to = self.download.save_to

        self.config.write_config()

        event.Skip()

        return True

    def on_url_change(self, event):
        self.ok = False
        if helper.is_url(self.url_text.GetValue().strip()):
            self.retrieve_btn.Enable()
        else:
            self.retrieve_btn.Disable()

    def on_url(self, event):
        self.filename_text.SetValue(_('正在获取信息...'))
        self.set_buttons(False)

        self.download.http_proxy = self.proxy_http_text.GetValue()
        self.download.https_proxy = self.proxy_https_text.GetValue()
        self.download.fetch_file_info(self.url_text.GetValue())
        filename = self.download.filename
        if filename:
            strsize = helper.strsize(self.download.size)
            self.filename_text.SetValue(filename)
            self.size_text.SetValue(strsize)
            self.ok = True
        else:
            self.filename_text.SetValue(self.download.status)
            self.size_text.SetValue('')
            self.ok = False

        self.set_buttons()

    def on_browse(self, event):
        defaultDir = self.path_text.GetValue() or os.getcwd()
        dlg = wx.DirDialog(self, _("选择文件夹"), defaultDir)

        if dlg.ShowModal() == wx.ID_OK:
            self.path_text.SetValue(dlg.GetPath())

    def clear(self):
        self.url_text.SetValue('')
        self.filename_text.SetValue('')
        self.size_text.SetValue('')
        self.download = Download(config=self.config)
