object QuickCompareDialog: TQuickCompareDialog
  Caption = 'Quick Compare'
  ClientHeight = 199
  ClientWidth = 385
  OnClose = FormClose
  OnCloseQuery = FormCloseQuery
  OnCreate = FormCreate
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object Image: TUiDlgIcon
    Left = 16
    Top = 16
    IconType = diApplication
  end
  object LeftSpecLbl: TUiLabel
    Left = 64
    Top = 16
    Width = 313
    Height = 13
    AutoSize = False
    Caption = '%'
    ShowAccelChar = False
  end
  object RightSpecLbl: TUiLabel
    Left = 64
    Top = 33
    Width = 313
    Height = 13
    AutoSize = False
    Caption = '%'
    ShowAccelChar = False
  end
  object QuickCompareLbl: TUiLabel
    Left = 64
    Top = 62
    Height = 13
    Caption = 'Quick Compare:'
  end
  object ResultsImage: TUiImage
    Left = 64
    Top = 79
    Width = 28
    Height = 16
    Images = BcImages.ContentImages
  end
  object ResultsLbl: TUiLabel
    Left = 92
    Top = 79
    Height = 13
    Caption = '%'
    FontStyle = [fsBold]
  end
  object SessionClassEdit: TUiComboBox
    Left = 8
    Top = 111
    Width = 135
    Height = 21
    Style = csDropDownList
    TabOrder = 0
    Images = BcImages.MainImages
    OnGetImageIndex = SessionClassEditGetImageIndex
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 135
    Width = 385
    Height = 64
    TabOrder = 1
    object QuickCompareShowBevel: TUiBevel
      Left = 0
      Top = 39
      Width = 385
      Height = 2
      Shape = bsTopLine
    end
    object OkBtn: TUiOkBtn
      Caption = 'Open &View'
      OnClick = OkClick
    end
    object CloseBtn: TUiCloseBtn
    end
    object QuickCompareShowEdit: TUiCheckBox
      Left = 8
      Top = 43
      Height = 17
      Caption = '&Show this dialog on file compare startup'
      TabOrder = 2
    end
  end
  object Timer: TTimer
    Interval = 500
    OnTimer = TimerTimer
    Left = 8
    Top = 8
  end
end
