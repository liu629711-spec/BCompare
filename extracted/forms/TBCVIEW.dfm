object BcView: TBcView
  object MessagePanel: TUiPanel
    Left = 0
    Top = 684
    Width = 750
    Height = 47
    Align = alBottom
    BevelOuter = bvNone
    BorderStyle = bsSingle
    Color = clInfoBk
    ParentBackground = False
    TabOrder = 0
    Visible = False
    object MessageImage: TUiDlgIcon
      Left = 8
      Top = 7
    end
    object MessageLbl: TUiLabel
      Left = 48
      Top = 17
      Height = 16
      Caption = '%'
      FontSize = 2
    end
    object MessageActionLinkLbl: TUiLinkLabel
      Left = 67
      Top = 17
      Height = 16
      Caption = '%'
      FontSize = 2
      URL = '%'
      Visible = False
    end
  end
  object StatusBar: TUiStatusBar
    Left = 0
    Top = 731
    Width = 750
    Height = 19
    AutoHint = True
    Panels = <
    >
    MacBottomBar = True
  end
end
