object DirSessionComparisonFrame: TDirSessionComparisonFrame
  HelpType = htKeyword
  HelpKeyword = 'SessionDirComparison'
  Caption = 'Comparison'
  object QuickLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = 'Quick tests:'
  end
  object TimestampToleranceLbl: TUiLabel
    Left = 90
    Top = 71
    Height = 13
    Caption = 'second to&lerance'
    FocusControl = TimestampToleranceEdit
    Transparent = True
  end
  object UseDOSAttrComparisonLbl: TUiLabel
    Left = 264
    Top = 25
    Height = 13
    Caption = 'Compare file attributes:'
    Transparent = True
  end
  object UseUnixAttrComparisonLbl: TUiLabel
    Left = 264
    Top = 71
    Height = 13
    Caption = 'Compare Unix metadata:'
    Transparent = True
  end
  object UseSizeComparisonEdit: TUiCheckBox
    Left = 8
    Top = 25
    Height = 17
    Caption = 'Compare file si&ze'
    TabOrder = 0
    OnClick = SomethingChangedClick
  end
  object UseTimestampComparisonEdit: TUiCheckBox
    Left = 8
    Top = 46
    Height = 17
    Caption = 'Compare &timestamps'
    TabOrder = 1
    OnClick = SomethingChangedClick
  end
  object TimestampToleranceEdit: TUiSpinEdit
    Left = 24
    Top = 67
    Width = 61
    Height = 21
    Max = 32767
    MaxLength = 5
    TabOrder = 2
    OnChange = SomethingChangedClick
  end
  object IgnoreDSTEdit: TUiCheckBox
    Left = 24
    Top = 92
    Height = 17
    Caption = '%'
    TabOrder = 3
    OnClick = SomethingChangedClick
  end
  object IgnoreTimeZoneEdit: TUiCheckBox
    Left = 24
    Top = 113
    Height = 17
    Caption = 'Ignore tim&ezone differences'
    TabOrder = 4
    OnClick = SomethingChangedClick
  end
  object UseCaseSensitiveComparisonEdit: TUiCheckBox
    Left = 8
    Top = 134
    Height = 17
    Caption = 'Compare filename &case'
    TabOrder = 5
    OnClick = SomethingChangedClick
  end
  object IgnoreFileExtsEdit: TUiCheckBox
    Left = 8
    Top = 155
    Height = 17
    Caption = 'Align filenames with different e&xtensions'
    TabOrder = 6
    OnClick = SomethingChangedClick
  end
  object NormalizedAlignmentEdit: TUiCheckBox
    Left = 8
    Top = 176
    Height = 17
    Caption = 'Align filenames with different Unicode normalization &forms'
    TabOrder = 7
    OnClick = SomethingChangedClick
  end
  object DOSAttrsEdit: TUiCheckListComboBox
    Left = 264
    Top = 42
    Width = 145
    Height = 21
    TabOrder = 8
    OnClickCheck = DOSAttrsClickCheck
  end
  object UsePermissionsComparisonEdit: TUiCheckBox
    Left = 264
    Top = 88
    Height = 17
    Caption = 'Compare permissions'
    TabOrder = 9
    OnClick = SomethingChangedClick
  end
  object UseOwnerComparisonEdit: TUiCheckBox
    Left = 264
    Top = 109
    Height = 17
    Caption = 'Compare owner'
    TabOrder = 10
    OnClick = SomethingChangedClick
  end
  object UseGroupComparisonEdit: TUiCheckBox
    Left = 264
    Top = 130
    Height = 17
    Caption = 'Compare group'
    TabOrder = 11
    OnClick = SomethingChangedClick
  end
  object FilePanel: TUiPanel
    Left = 0
    Top = 201
    Width = 425
    Height = 155
    BevelOuter = bvNone
    TabOrder = 12
    object FileBevel: TUiBevel
      Left = 8
      Top = 0
      Width = 409
      Height = 1
      Shape = bsTopLine
    end
    object FileLbl: TUiLabel
      Left = 8
      Top = 8
      Height = 13
      Caption = 'Requires opening files:'
    end
    object UseContentComparisonEdit: TUiCheckBox
      Left = 8
      Top = 25
      Height = 17
      Caption = 'Compare co&ntents:'
      TabOrder = 0
      OnClick = SomethingChangedClick
    end
    object CRC32Edit: TUiRadioButton
      Left = 24
      Top = 46
      Height = 17
      Caption = 'C&RC comparison'
      TabOrder = 1
      OnClick = SomethingChangedClick
    end
    object BinaryEdit: TUiRadioButton
      Left = 24
      Top = 67
      Height = 17
      Caption = 'Binar&y comparison'
      TabOrder = 2
      OnClick = SomethingChangedClick
    end
    object RulesBasedEdit: TUiRadioButton
      Left = 24
      Top = 88
      Height = 17
      Caption = 'R&ules-based comparison'
      TabOrder = 3
      OnClick = SomethingChangedClick
    end
    object ContentCompareSkipSameEdit: TUiCheckBox
      Left = 24
      Top = 109
      Height = 17
      Caption = 'Ski&p if quick tests indicate files are the same'
      TabOrder = 4
      OnClick = SomethingChangedClick
    end
    object ContentCompareOverridesEdit: TUiCheckBox
      Left = 8
      Top = 130
      Height = 17
      Caption = 'Override &quick test results'
      TabOrder = 5
      OnClick = SomethingChangedClick
    end
    object UseVersionComparisonEdit: TUiCheckBox
      Left = 264
      Top = 25
      Height = 17
      Caption = 'Compare &versions'
      TabOrder = 6
      OnClick = SomethingChangedClick
    end
  end
end
