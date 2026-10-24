object TextWeightItemDialog: TTextWeightItemDialog
  Caption = 'Line Weight'
  ClientHeight = 155
  ClientWidth = 329
  OnCreate = FormCreate
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object FindStrLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = '&Text matching:'
    FocusControl = FindStrEdit
  end
  object FindREBtn: TUiSpeedButton
    Left = 224
    Top = 25
    Hint = 'Insert Regular Expression Element'
    DropDown = True
    Flat = False
    PopupMenu = FindREPopup
  end
  object PriorityLbl: TUiLabel
    Left = 256
    Top = 8
    Height = 13
    Caption = '&Priority:'
    FocusControl = PriorityEdit
  end
  object FindStrEdit: TUiEdit
    Left = 8
    Top = 25
    Width = 209
    Height = 21
    TabOrder = 0
    OnChange = SomethingChangedClick
  end
  object PriorityEdit: TUiComboBox
    Left = 256
    Top = 25
    Width = 65
    Height = 21
    Style = csDropDownList
    TabOrder = 1
    OnChange = SomethingChangedClick
  end
  object CaseSensitiveEdit: TUiCheckBox
    Left = 8
    Top = 54
    Height = 17
    Caption = 'Match character &case'
    TabOrder = 2
    OnClick = SomethingChangedClick
  end
  object WholeWordsEdit: TUiCheckBox
    Left = 8
    Top = 75
    Height = 17
    Caption = '&Whole words only'
    TabOrder = 3
    OnClick = SomethingChangedClick
  end
  object IsRegExpEdit: TUiCheckBox
    Left = 8
    Top = 96
    Height = 17
    Caption = 'Regular e&xpression'
    TabOrder = 4
    OnClick = SomethingChangedClick
  end
  object REHelpBtn: TUiButton
    Left = 243
    Top = 93
    Width = 78
    HelpType = htKeyword
    HelpKeyword = 'Sample_Regular_Expressions'
    Caption = 'RE Example&s'
    TabOrder = 5
    AutoSize = asRight
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 116
    Width = 329
    TabOrder = 6
    object OkBtn: TUiOkBtn
      OnClick = OkClick
    end
    object CancelBtn: TUiCancelBtn
    end
  end
  object FindREPopup: TUiPopupMenu
    Left = 8
    Top = 8
    object TabItem: TUiMenuItem
      Caption = 'Tab Character (\t)'
      OnClick = FindREItemClick
    end
    object AnyItem: TUiMenuItem
      Caption = 'Any Character (.)'
      OnClick = FindREItemClick
    end
    object AlphaItem: TUiMenuItem
      Caption = 'Any Alphanumeric Character (\w)'
      OnClick = FindREItemClick
    end
    object NonAlphaItem: TUiMenuItem
      Caption = 'Any Non-alphanumeric Character (\W)'
      OnClick = FindREItemClick
    end
    object NumItem: TUiMenuItem
      Caption = 'Any Numeric Character (\d)'
      OnClick = FindREItemClick
    end
    object NonNumItem: TUiMenuItem
      Caption = 'Any Non-numeric Character (\D)'
      OnClick = FindREItemClick
    end
    object WSItem: TUiMenuItem
      Caption = 'Any Whitespace Character (\s)'
      OnClick = FindREItemClick
    end
    object CharSetItem: TUiMenuItem
      Caption = 'Character in Set ([])'
      OnClick = FindREItemClick
    end
    object NotCharSetItem: TUiMenuItem
      Caption = 'Character Not in Set ([^])'
      OnClick = FindREItemClick
    end
    object BeginItem: TUiMenuItem
      Caption = 'Beginning of Line (^)'
      OnClick = FindREItemClick
    end
    object EndItem: TUiMenuItem
      Caption = 'End of Line ($)'
      OnClick = FindREItemClick
    end
    object TaggedItem: TUiMenuItem
      Caption = 'Tagged Expression (())'
      OnClick = FindREItemClick
    end
    object OrItem: TUiMenuItem
      Caption = 'Or (|)'
      OnClick = FindREItemClick
    end
    object ZeroOrMoreItem: TUiMenuItem
      Caption = '0 Or More Matches (*)'
      OnClick = FindREItemClick
    end
    object OneOrMoreItem: TUiMenuItem
      Caption = '1 Or More Matches (+)'
      OnClick = FindREItemClick
    end
    object ZeroOrOneItem: TUiMenuItem
      Caption = '0 Or 1 Matches (?)'
      OnClick = FindREItemClick
    end
  end
end
