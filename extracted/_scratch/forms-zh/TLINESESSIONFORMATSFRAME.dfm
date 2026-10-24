object LineSessionFormatsFrame: TLineSessionFormatsFrame
  HelpType = htKeyword
  object CodePagePanel: TUiPanel
    Left = 0
    Top = 125
    Width = 425
    Height = 146
    BevelOuter = bvNone
    TabOrder = 3
    object CodePageBevel: TUiBevel
      Left = 8
      Top = 0
      Width = 409
      Height = 1
      Shape = bsTopLine
    end
    object LeftCodePageLbl: TUiLabel
      Left = 8
      Top = 8
      Height = 13
      Caption = 'L&eft encoding override:'
      FocusControl = LeftCodePageEdit
    end
    object RightCodePageLbl: TUiLabel
      Left = 8
      Top = 54
      Height = 13
      Caption = 'Ri&ght encoding override:'
      FocusControl = RightCodePageEdit
    end
    object CenterCodePageLbl: TUiLabel
      Left = 8
      Top = 100
      Height = 13
      Caption = '&Center encoding override:'
      FocusControl = CenterCodePageEdit
    end
    object LeftCodePageEdit: TUiCodePageEdit
      Left = 8
      Top = 25
      Width = 409
      Height = 21
      TabOrder = 0
      OnChange = SomethingChangedClick
      UseNone = True
    end
    object RightCodePageEdit: TUiCodePageEdit
      Left = 8
      Top = 71
      Width = 409
      Height = 21
      TabOrder = 1
      OnChange = SomethingChangedClick
      UseNone = True
    end
    object CenterCodePageEdit: TUiCodePageEdit
      Left = 8
      Top = 117
      Width = 409
      Height = 21
      TabOrder = 2
      OnChange = SomethingChangedClick
      UseNone = True
    end
  end
end
