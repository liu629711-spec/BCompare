object FileFormatGeneralFrame: TFileFormatGeneralFrame
  Caption = 'General'
  object MaskLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = '&Mask:'
    FocusControl = MaskEdit
  end
  object DescriptionLbl: TUiLabel
    Left = 8
    Top = 54
    Height = 13
    Caption = 'D&escription:'
    FocusControl = DescriptionEdit
  end
  object MaskEdit: TUiEdit
    Left = 8
    Top = 25
    Width = 257
    Height = 21
    TabOrder = 0
    OnChange = SomethingChangedClick
  end
  object DescriptionEdit: TUiMemo
    Left = 8
    Top = 71
    Width = 257
    Height = 242
    ScrollBars = ssVertical
    TabOrder = 1
    OnChange = SomethingChangedClick
  end
end
