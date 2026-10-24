object TextGrammarItemDialog: TTextGrammarItemDialog
  HelpType = htKeyword
  HelpKeyword = 'DlgTextGrammarItem'
  BorderIcons = [biSystemMenu, biHelp]
  Caption = 'Grammar Item'
  ClientHeight = 293
  ClientWidth = 542
  OnCreate = FormCreate
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object ElementLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = '&Element name:'
    FocusControl = ElementEdit
  end
  object CategoryLbl: TUiLabel
    Left = 8
    Top = 54
    Height = 13
    Caption = 'Category:'
  end
  object ElementEdit: TUiComboBox
    Left = 8
    Top = 25
    Width = 169
    Height = 21
    TabOrder = 0
    OnChange = SomethingChangedClick
  end
  object CategoryBasicEdit: TUiRadioButton
    Left = 8
    Top = 71
    Height = 17
    Caption = 'B&asic'
    TabOrder = 1
    OnClick = CategoryClick
  end
  object CategoryDelimitedEdit: TUiRadioButton
    Left = 8
    Top = 92
    Height = 17
    Caption = '&Delimited'
    TabOrder = 2
    OnClick = CategoryClick
  end
  object CategoryListEdit: TUiRadioButton
    Left = 8
    Top = 113
    Height = 17
    Caption = '&List'
    TabOrder = 3
    OnClick = CategoryClick
  end
  object CategoryColumnsEdit: TUiRadioButton
    Left = 8
    Top = 134
    Height = 17
    Caption = 'Col&umns'
    TabOrder = 4
    OnClick = CategoryClick
  end
  object CategoryLinesEdit: TUiRadioButton
    Left = 8
    Top = 155
    Height = 17
    Caption = 'L&ines'
    TabOrder = 5
    OnClick = CategoryClick
  end
  object PanelView: TUiActivePanelView
    Left = 177
    Top = 0
    Width = 365
    Height = 237
    TabOrder = 6
    object BasicPanel: TUiActivePanel
      object BasicLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 13
        Caption = '&Text matching:'
        FocusControl = BasicEdit
      end
      object BasicREBtn: TUiSpeedButton
        Left = 334
        Top = 25
        Hint = 'Insert Regular Expression Element'
        DropDown = True
        Flat = False
        PopupMenu = REPopup
      end
      object BasicEdit: TUiEdit
        Left = 8
        Top = 25
        Width = 318
        Height = 21
        TabOrder = 0
        OnChange = SomethingChangedClick
      end
      object BasicCaseSensitiveEdit: TUiCheckBox
        Left = 8
        Top = 54
        Height = 17
        Caption = 'Match character &case'
        TabOrder = 1
        OnClick = SomethingChangedClick
      end
      object BasicIsRegExpEdit: TUiCheckBox
        Left = 8
        Top = 75
        Height = 17
        Caption = 'Regular e&xpression'
        TabOrder = 2
        OnClick = SomethingChangedClick
      end
      object BasicREHelpBtn: TUiButton
        Left = 279
        Top = 72
        Width = 78
        HelpType = htKeyword
        HelpKeyword = 'Sample_Regular_Expressions'
        Caption = 'RE Example&s'
        TabOrder = 3
        AutoSize = asRight
      end
    end
    object DelimitedPanel: TUiActivePanel
      object DelimitedLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 13
        Caption = '&Text from:'
        FocusControl = DelimitedEdit
      end
      object DelimitedREBtn: TUiSpeedButton
        Left = 334
        Top = 25
        Hint = 'Insert Regular Expression Element'
        DropDown = True
        Flat = False
        PopupMenu = REPopup
      end
      object DelimitedStopLbl: TUiLabel
        Left = 8
        Top = 54
        Height = 13
        Caption = 't&o:'
        FocusControl = DelimitedStopEdit
      end
      object DelimitedStopREBtn: TUiSpeedButton
        Left = 334
        Top = 71
        Hint = 'Insert Regular Expression Element'
        DropDown = True
        Flat = False
        PopupMenu = REPopup
      end
      object DelimitedEscapeLbl: TUiLabel
        Left = 8
        Top = 100
        Height = 13
        Caption = 'Esca&pe character:'
        FocusControl = DelimitedEscapeEdit
      end
      object DelimitedEdit: TUiEdit
        Left = 8
        Top = 25
        Width = 318
        Height = 21
        TabOrder = 0
        OnChange = SomethingChangedClick
      end
      object DelimitedStopEdit: TUiEdit
        Left = 8
        Top = 71
        Width = 318
        Height = 21
        TabOrder = 1
        OnChange = SomethingChangedClick
      end
      object DelimitedEscapeEdit: TUiEdit
        Left = 8
        Top = 117
        Width = 33
        Height = 21
        MaxLength = 1
        TabOrder = 2
        OnChange = SomethingChangedClick
      end
      object DelimitedStopEOLEdit: TUiCheckBox
        Left = 8
        Top = 146
        Height = 17
        Caption = 'Stop at e&nd of line'
        TabOrder = 3
        OnClick = SomethingChangedClick
      end
      object DelimitedCaseSensitiveEdit: TUiCheckBox
        Left = 8
        Top = 167
        Height = 17
        Caption = 'Match character &case'
        TabOrder = 4
        OnClick = SomethingChangedClick
      end
      object DelimitedIsRegExpEdit: TUiCheckBox
        Left = 8
        Top = 188
        Height = 17
        Caption = 'Regular e&xpressions'
        TabOrder = 5
        OnClick = SomethingChangedClick
      end
      object DelimitedREHelpBtn: TUiButton
        Left = 279
        Top = 185
        Width = 78
        HelpType = htKeyword
        HelpKeyword = 'Sample_Regular_Expressions'
        Caption = 'RE Example&s'
        TabOrder = 6
        AutoSize = asRight
      end
    end
    object ListPanel: TUiActivePanel
      object ListLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 13
        Caption = '&Text in list:'
        FocusControl = ListItemsEdit
      end
      object ListREBtn: TUiSpeedButton
        Left = 334
        Top = 25
        Hint = 'Insert Regular Expression Element'
        DropDown = True
        Flat = False
        PopupMenu = REPopup
      end
      object ListItemsEdit: TUiMemo
        Left = 8
        Top = 25
        Width = 318
        Height = 153
        ScrollBars = ssVertical
        TabOrder = 0
        WordWrap = False
        OnChange = SomethingChangedClick
      end
      object ListCaseSensitiveEdit: TUiCheckBox
        Left = 8
        Top = 186
        Height = 17
        Caption = 'Match character &case'
        TabOrder = 1
        OnClick = SomethingChangedClick
      end
      object ListIsRegExpEdit: TUiCheckBox
        Left = 8
        Top = 207
        Height = 17
        Caption = 'Regular e&xpressions'
        TabOrder = 2
        OnClick = SomethingChangedClick
      end
      object ListREHelpBtn: TUiButton
        Left = 279
        Top = 204
        Width = 78
        HelpType = htKeyword
        HelpKeyword = 'Sample_Regular_Expressions'
        Caption = 'RE Example&s'
        TabOrder = 3
        AutoSize = asRight
      end
    end
    object ColumnsPanel: TUiActivePanel
      object ColumnsLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 13
        Caption = '&Text from column:'
        FocusControl = ColumnsEdit
      end
      object ColumnsStopLbl: TUiLabel
        Left = 8
        Top = 54
        Height = 13
        Caption = 't&o column:'
        FocusControl = ColumnsStopEdit
      end
      object ColumnsEdit: TUiSpinEdit
        Left = 8
        Top = 25
        Width = 50
        Height = 21
        Min = 1
        Position = 1
        TabOrder = 0
        OnChange = SomethingChangedClick
      end
      object ColumnsStopEdit: TUiSpinEdit
        Left = 8
        Top = 71
        Width = 50
        Height = 21
        Min = 1
        Position = 1
        TabOrder = 1
        OnChange = SomethingChangedClick
      end
      object ColumnsStopEOLEdit: TUiCheckBox
        Left = 8
        Top = 100
        Height = 17
        Caption = 'to e&nd of line'
        TabOrder = 2
        OnClick = SomethingChangedClick
      end
    end
    object LinesPanel: TUiActivePanel
      object LinesLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 13
        Caption = '&Text matching:'
        FocusControl = LinesEdit
      end
      object LinesREBtn: TUiSpeedButton
        Left = 334
        Top = 25
        Hint = 'Insert Regular Expression Element'
        DropDown = True
        Flat = False
        PopupMenu = REPopup
      end
      object LinesCountLbl: TUiLabel
        Left = 8
        Top = 79
        Height = 13
        Caption = 'and &next:'
        FocusControl = LinesCountEdit
      end
      object LinesCountLinesLbl: TUiLabel
        Left = 64
        Top = 100
        Height = 13
        Caption = 'lines'
        FocusControl = LinesCountEdit
      end
      object LinesEdit: TUiEdit
        Left = 8
        Top = 25
        Width = 318
        Height = 21
        TabOrder = 0
        OnChange = SomethingChangedClick
      end
      object Lines1Edit: TUiCheckBox
        Left = 8
        Top = 54
        Height = 17
        Caption = '&or line 1'
        TabOrder = 1
        OnClick = SomethingChangedClick
      end
      object LinesCountEdit: TUiSpinEdit
        Left = 8
        Top = 96
        Width = 50
        Height = 21
        Position = 1
        TabOrder = 2
        OnChange = SomethingChangedClick
      end
      object LinesCaseSensitiveEdit: TUiCheckBox
        Left = 8
        Top = 125
        Height = 17
        Caption = 'Match character &case'
        TabOrder = 3
        OnClick = SomethingChangedClick
      end
      object LinesIsRegExpEdit: TUiCheckBox
        Left = 8
        Top = 146
        Height = 17
        Caption = 'Regular e&xpression'
        TabOrder = 4
        OnClick = SomethingChangedClick
      end
      object LinesREHelpBtn: TUiButton
        Left = 279
        Top = 143
        Width = 78
        HelpType = htKeyword
        HelpKeyword = 'Sample_Regular_Expressions'
        Caption = 'RE Example&s'
        TabOrder = 5
        AutoSize = asRight
      end
    end
  end
  object ElementCaseSigEdit: TUiCheckBox
    Left = 185
    Top = 237
    Height = 17
    Caption = 'This element is case sensiti&ve'
    TabOrder = 7
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 254
    Width = 542
    TabOrder = 8
    object OkBtn: TUiOkBtn
      OnClick = OkClick
    end
    object CancelBtn: TUiCancelBtn
    end
    object HelpBtn: TUiHelpBtn
    end
  end
  object REPopup: TUiPopupMenu
    Left = 8
    Top = 8
    object TabItem: TUiMenuItem
      Caption = 'Tab Character (\t)'
      OnClick = REItemClick
    end
    object AnyItem: TUiMenuItem
      Caption = 'Any Character (.)'
      OnClick = REItemClick
    end
    object AlphaItem: TUiMenuItem
      Caption = 'Any Alphanumeric Character (\w)'
      OnClick = REItemClick
    end
    object NonAlphaItem: TUiMenuItem
      Caption = 'Any Non-alphanumeric Character (\W)'
      OnClick = REItemClick
    end
    object NumItem: TUiMenuItem
      Caption = 'Any Numeric Character (\d)'
      OnClick = REItemClick
    end
    object NonNumItem: TUiMenuItem
      Caption = 'Any Non-numeric Character (\D)'
      OnClick = REItemClick
    end
    object WSItem: TUiMenuItem
      Caption = 'Any Whitespace Character (\s)'
      OnClick = REItemClick
    end
    object CharSetItem: TUiMenuItem
      Caption = 'Character in Set ([])'
      OnClick = REItemClick
    end
    object NotCharSetItem: TUiMenuItem
      Caption = 'Character Not in Set ([^])'
      OnClick = REItemClick
    end
    object BeginItem: TUiMenuItem
      Caption = 'Beginning of Line (^)'
      OnClick = REItemClick
    end
    object EndItem: TUiMenuItem
      Caption = 'End of Line ($)'
      OnClick = REItemClick
    end
    object FormFeedItem: TUiMenuItem
      Caption = 'Form Feed Character (\xc)'
      OnClick = REItemClick
    end
    object OrItem: TUiMenuItem
      Caption = 'Or (|)'
      OnClick = REItemClick
    end
    object ZeroOrMoreItem: TUiMenuItem
      Caption = '0 Or More Matches (*)'
      OnClick = REItemClick
    end
    object OneOrMoreItem: TUiMenuItem
      Caption = '1 Or More Matches (+)'
      OnClick = REItemClick
    end
    object ZeroOrOneItem: TUiMenuItem
      Caption = '0 Or 1 Matches (?)'
      OnClick = REItemClick
    end
  end
end
