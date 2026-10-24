object TableFormatTypeFrame: TTableFormatTypeFrame
  HelpType = htKeyword
  HelpKeyword = 'FormatTableType'
  Caption = 'Type'
  object FmtFrame: TTableFmtFrame
    Left = 0
    Top = 0
    Width = 273
    Height = 238
    TabOrder = 0
    OnResize = FmtFrameResize
  end
  object FirstKindPanel: TUiPanel
    Left = 0
    Top = 238
    Width = 273
    Height = 54
    BevelOuter = bvNone
    TabOrder = 1
    object FirstKindBevel: TUiBevel
      Left = 8
      Top = 0
      Width = 257
      Height = 1
      Shape = bsTopLine
    end
    object FirstKindLbl: TUiLabel
      Left = 8
      Top = 8
      Height = 13
      Caption = 'Fi&rst line contains:'
      FocusControl = FirstKindEdit
    end
    object FirstKindEdit: TUiComboBox
      Left = 8
      Top = 25
      Width = 102
      Height = 21
      Style = csDropDownList
      TabOrder = 0
      OnChange = SomethingChangedClick
      Items.Strings = ('Detect', 'Column names', 'Cell data')
    end
  end
end
