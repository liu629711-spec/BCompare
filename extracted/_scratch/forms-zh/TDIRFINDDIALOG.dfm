object DirFindDialog: TDirFindDialog
  HelpType = htKeyword
  HelpKeyword = 'DlgDirFind'
  BorderIcons = [biSystemMenu, biHelp]
  Caption = 'Find Filename'
  ClientHeight = 278
  ClientWidth = 337
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object FindPanel: TUiPanel
    Left = 0
    Top = 0
    Width = 337
    Height = 54
    Align = alTop
    BevelOuter = bvNone
    TabOrder = 0
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
    object FindStrEdit: TUiComboBox
      Left = 8
      Top = 25
      Width = 290
      Height = 21
      TabOrder = 0
      OnChange = SomethingChangedClick
      IsMRU = True
    end
  end
  object OptionsPanel: TUiPanel
    Left = 0
    Top = 54
    Width = 337
    Height = 185
    Align = alTop
    BevelOuter = bvNone
    TabOrder = 1
    object SidesLbl: TUiLabel
      Left = 8
      Top = 109
      Height = 13
      Caption = 'Sides:'
      FocusControl = FindStrEdit
    end
    object CaseSensitiveEdit: TUiCheckBox
      Left = 8
      Top = 0
      Height = 17
      Caption = 'Match character &case'
      TabOrder = 0
      OnClick = SomethingChangedClick
    end
    object WholeWordsEdit: TUiCheckBox
      Left = 8
      Top = 21
      Height = 17
      Caption = '&Whole words only'
      TabOrder = 1
      OnClick = SomethingChangedClick
    end
    object IsRegExpEdit: TUiCheckBox
      Left = 8
      Top = 42
      Height = 17
      Caption = 'Regular e&xpression'
      TabOrder = 2
      OnClick = SomethingChangedClick
    end
    object REHelpBtn: TUiButton
      Left = 251
      Top = 39
      Width = 78
      HelpType = htKeyword
      HelpKeyword = 'Sample_Regular_Expressions'
      Caption = 'RE Example&s'
      TabOrder = 3
      AutoSize = asRight
    end
    object WrapEdit: TUiCheckBox
      Left = 8
      Top = 63
      Height = 17
      Caption = 'Wra&p search'
      TabOrder = 4
      OnClick = SomethingChangedClick
    end
    object UpEdit: TUiCheckBox
      Left = 8
      Top = 84
      Height = 17
      Caption = 'Search &up'
      TabOrder = 5
      OnClick = SomethingChangedClick
    end
    object LeftSideEdit: TUiCheckBox
      Left = 8
      Top = 126
      Height = 17
      Caption = '&Left'
      TabOrder = 6
      OnClick = SideEditClick
    end
    object CenterSideEdit: TUiCheckBox
      Left = 8
      Top = 147
      Height = 17
      Caption = 'Ce&nter'
      TabOrder = 7
      OnClick = SideEditClick
    end
    object RightSideEdit: TUiCheckBox
      Left = 8
      Top = 168
      Height = 17
      Caption = '&Right'
      TabOrder = 8
      OnClick = SideEditClick
    end
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 239
    Width = 337
    TabOrder = 2
    object OkBtn: TUiOkBtn
      OnClick = OkClick
    end
    object SelectAllBtn: TUiYesToAllBtn
      Caption = 'Select &All'
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
end
