object ProfileFileSaveDialog: TProfileFileSaveDialog
  Caption = 'Save File Using Profile'
  PixelsPerInch = 96
  TextHeight = 13
  object LeftBevel: TUiBevel
    Height = 179
  end
  object RightBevel: TUiBevel
    Height = 179
  end
  object ListView: TUiListView
    Height = 179
  end
  object NamePanel: TUiPanel
    Top = 216
  end
  object BtnPanel: TUiBtnPanel
    TabOrder = 4
  end
  object TextPanel: TUiPanel
    Left = 0
    Top = 274
    Width = 362
    Height = 58
    Align = alBottom
    BevelOuter = bvNone
    TabOrder = 3
    DesignSize = (362, 58)
    object CodePageLbl: TUiLabel
      Left = 8
      Top = 12
      Height = 13
      Caption = '&Encoding:'
      FocusControl = CodePageEdit
    end
    object LineEndingStyleLbl: TUiLabel
      Left = 8
      Top = 41
      Height = 13
      Caption = '&Line ending style:'
      FocusControl = LineEndingStyleEdit
    end
    object CodePageEdit: TUiCodePageEdit
      Left = 79
      Top = 8
      Width = 274
      Height = 21
      Anchors = [akLeft, akTop, akRight]
      TabOrder = 0
      AllowDetect = False
    end
    object LineEndingStyleEdit: TUiComboBox
      Left = 79
      Top = 37
      Width = 274
      Height = 21
      Style = csDropDownList
      Anchors = [akLeft, akTop, akRight]
      TabOrder = 1
    end
  end
end
