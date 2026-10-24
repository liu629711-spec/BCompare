object TextReplacementItemDialog: TTextReplacementItemDialog
  HelpType = htKeyword
  HelpKeyword = 'DlgTextReplacementItem'
  BorderIcons = [biSystemMenu, biHelp]
  Caption = 'Replacement Item'
  ClientHeight = 236
  ClientWidth = 337
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object FindStrLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = '&Text to find:'
    FocusControl = FindStrEdit
  end
  object FindREBtn: TUiSpeedButton
    Left = 306
    Top = 25
    Hint = 'Insert Regular Expression Element'
    DropDown = True
    Flat = False
    PopupMenu = FindREPopup
  end
  object ReplaceStrLbl: TUiLabel
    Left = 8
    Top = 54
    Height = 13
    Caption = 'R&eplace with:'
    FocusControl = ReplaceStrEdit
  end
  object ReplaceREBtn: TUiSpeedButton
    Left = 306
    Top = 71
    Hint = 'Insert Regular Expression Element'
    DropDown = True
    Flat = False
    PopupMenu = ReplaceREPopup
  end
  object FindStrEdit: TUiEdit
    Left = 8
    Top = 25
    Width = 290
    Height = 21
    TabOrder = 0
    OnChange = SomethingChangedClick
  end
  object ReplaceStrEdit: TUiEdit
    Left = 8
    Top = 71
    Width = 290
    Height = 21
    TabOrder = 1
    OnChange = SomethingChangedClick
  end
  object CaseSensitiveEdit: TUiCheckBox
    Left = 8
    Top = 100
    Height = 17
    Caption = 'Match character &case'
    TabOrder = 2
    OnClick = SomethingChangedClick
  end
  object WholeWordsEdit: TUiCheckBox
    Left = 8
    Top = 121
    Height = 17
    Caption = '&Whole words only'
    TabOrder = 3
    OnClick = SomethingChangedClick
  end
  object IsRegExpEdit: TUiCheckBox
    Left = 8
    Top = 142
    Height = 17
    Caption = 'Regular e&xpression'
    TabOrder = 4
    OnClick = SomethingChangedClick
  end
  object REHelpBtn: TUiButton
    Left = 251
    Top = 139
    Width = 78
    HelpType = htKeyword
    HelpKeyword = 'Sample_Regular_Expressions'
    Caption = 'RE Example&s'
    TabOrder = 5
    AutoSize = asRight
  end
  object IsSrcPanel: TUiPanel
    Left = 8
    Top = 163
    Width = 321
    Height = 34
    BevelOuter = bvNone
    TabOrder = 6
    object IsSrcLbl: TUiLabel
      Left = 0
      Top = 0
      Height = 13
      Caption = 'Side:'
    end
    object LeftIsSrcEdit: TUiRadioButton
      Left = 0
      Top = 17
      Height = 17
      Caption = '&Left'
      TabOrder = 0
      OnClick = SomethingChangedClick
    end
    object RightIsSrcEdit: TUiRadioButton
      Left = 160
      Top = 17
      Height = 17
      Caption = '&Right'
      TabOrder = 1
      OnClick = SomethingChangedClick
    end
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 197
    Width = 337
    TabOrder = 7
    object OkBtn: TUiOkBtn
      OnClick = OkClick
    end
    object CancelBtn: TUiCancelBtn
    end
  end
  object FindREPopup: TUiPopupMenu
    Left = 8
    Top = 8
    object FindTabItem: TUiMenuItem
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
  object ReplaceREPopup: TUiPopupMenu
    Left = 40
    Top = 8
    object ReplaceTabItem: TUiMenuItem
      Caption = 'Tab Character (\t)'
      OnClick = ReplaceREItemClick
    end
    object FindStrItem: TUiMenuItem
      Caption = 'Find Expression ($0)'
      OnClick = ReplaceREItemClick
    end
    object Tagged1Item: TUiMenuItem
      Caption = 'Tagged Expression 1 ($1)'
      OnClick = ReplaceREItemClick
    end
    object Tagged2Item: TUiMenuItem
      Caption = 'Tagged Expression 2 ($2)'
      OnClick = ReplaceREItemClick
    end
    object Tagged3Item: TUiMenuItem
      Caption = 'Tagged Expression 3 ($3)'
      OnClick = ReplaceREItemClick
    end
    object Tagged4Item: TUiMenuItem
      Caption = 'Tagged Expression 4 ($4)'
      OnClick = ReplaceREItemClick
    end
    object Tagged5Item: TUiMenuItem
      Caption = 'Tagged Expression 5 ($5)'
      OnClick = ReplaceREItemClick
    end
    object Tagged6Item: TUiMenuItem
      Caption = 'Tagged Expression 6 ($6)'
      OnClick = ReplaceREItemClick
    end
    object Tagged7Item: TUiMenuItem
      Caption = 'Tagged Expression 7 ($7)'
      OnClick = ReplaceREItemClick
    end
    object Tagged8Item: TUiMenuItem
      Caption = 'Tagged Expression 8 ($8)'
      OnClick = ReplaceREItemClick
    end
    object Tagged9Item: TUiMenuItem
      Caption = 'Tagged Expression 9 ($9)'
      OnClick = ReplaceREItemClick
    end
  end
end
