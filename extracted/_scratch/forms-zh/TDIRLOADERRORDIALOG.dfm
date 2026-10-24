object DirLoadErrorDialog: TDirLoadErrorDialog
  BorderStyle = bsSizeable
  Caption = 'Folder Not Available'
  ClientHeight = 69
  ClientWidth = 405
  Constraints.MaxHeight = 104
  Constraints.MinHeight = 104
  Constraints.MinWidth = 265
  OnCloseQuery = FormCloseQuery
  AllowDropFiles = True
  OnDropFiles = FormDropFiles
  PixelsPerInch = 96
  TextHeight = 13
  object DirEdit: TUiSpecComboBar
    Left = 8
    Top = 8
    Width = 389
    Anchors = [akLeft, akTop, akRight]
    AutoCompleteEx = acDirs
    Images = BcImages.MainImages
    SupportsProfile = True
    TabOrder = 0
    OnBrowse = DirEditBrowse
    OnUpdateTitles = DirEditUpdateTitles
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 30
    Width = 405
    TabOrder = 1
    SizeGripper = True
    ItemTabOrder0 = False
    object CreateBtn: TUiButton
      Left = 8
      Top = 8
      Caption = '&Create'
      TabOrder = 0
      OnClick = CreateClick
      AutoSize = asLeft
    end
    object OkBtn: TUiOkBtn
      Caption = '&Retry'
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
