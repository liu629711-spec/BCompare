object LineFileFormatConversionFrame: TLineFileFormatConversionFrame
  object CodePageLbl: TUiLabel
    Left = 8
    Top = 158
    Height = 13
    Caption = '&Encoding:'
    FocusControl = CodePageEdit
  end
  object CodePageBevel: TUiBevel
    Left = 8
    Top = 150
    Width = 257
    Height = 1
    Shape = bsTopLine
  end
  object CodePageEdit: TUiCodePageEdit
    Left = 8
    Top = 175
    Width = 257
    Height = 21
    TabOrder = 4
    OnChange = SomethingChangedClick
  end
  object CtrlZIsEOFEdit: TUiCheckBox
    Left = 8
    Top = 204
    Height = 17
    Caption = 'Ctrl+&Z indicates end of file'
    TabOrder = 5
    OnClick = SomethingChangedClick
  end
end
