object TipDialog: TTipDialog
  Caption = 'Tip'
  ClientHeight = 282
  ClientWidth = 337
  Color = clWindow
  OnClose = FormClose
  OnCreate = FormCreate
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object Image: TUiDlgIcon
    Left = 16
    Top = 16
    IconType = diInformation
  end
  object BottomLineBevel: TUiBevel
    Left = 0
    Top = 216
    Width = 337
    Height = 2
    Align = alBottom
    Shape = bsBottomLine
    Style = bsRaised
  end
  object Panel: TUiPanel
    Left = 64
    Top = 16
    Width = 265
    Height = 200
    BevelOuter = bvNone
    ParentColor = True
    TabOrder = 0
    object TitleBevel: TUiBevel
      Left = 0
      Top = 0
      Width = 265
      Height = 8
      Align = alTop
      Shape = bsSpacer
    end
    object TitleLbl: TUiLabel
      Left = 0
      Top = 8
      Height = 16
      Align = alTop
      Caption = '%'
      FontSize = 2
    end
    object CommentsBevel: TUiBevel
      Left = 0
      Top = 24
      Width = 265
      Height = 16
      Align = alTop
      Shape = bsSpacer
    end
    object CommentsLbl: TUiLabel
      Left = 0
      Top = 40
      Width = 265
      Height = 13
      Align = alTop
      Caption = '%'
      WordWrap = True
    end
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 218
    Width = 337
    Height = 64
    ParentBackground = False
    TabOrder = 1
    object DontShowAgainBevel: TUiBevel
      Left = 0
      Top = 39
      Width = 337
      Height = 2
      Shape = bsTopLine
    end
    object CloseBtn: TUiCloseBtn
    end
    object DontShowAgainEdit: TUiCheckBox
      Left = 8
      Top = 43
      Height = 17
      Caption = '&Don''t show again'
      TabOrder = 1
    end
  end
end
