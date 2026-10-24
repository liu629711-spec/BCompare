object DirOtherFilterItemDialog: TDirOtherFilterItemDialog
  HelpType = htKeyword
  HelpKeyword = 'DlgDirOtherFilterItem'
  BorderIcons = [biSystemMenu, biHelp]
  Caption = 'Other Filter'
  ClientHeight = 244
  ClientWidth = 536
  OnCreate = FormCreate
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object LeftBevel: TUiBevel
    Left = 178
    Top = 8
    Width = 2
    Height = 197
    Shape = bsLeftLine
  end
  object LeftPanel: TPanel
    Left = 0
    Top = 0
    Width = 175
    Height = 205
    BevelOuter = bvNone
    TabOrder = 0
    object KindLbl: TUiLabel
      Left = 8
      Top = 8
      Height = 13
      Caption = 'Filter on:'
    end
    object KindDateEdit: TUiRadioButton
      Left = 8
      Top = 25
      Height = 17
      Caption = 'Date &modified'
      TabOrder = 0
      OnClick = KindEditChange
    end
    object KindSizeEdit: TUiRadioButton
      Left = 8
      Top = 46
      Height = 17
      Caption = '&Size'
      TabOrder = 1
      OnClick = KindEditChange
    end
    object KindContentEdit: TUiRadioButton
      Left = 8
      Top = 67
      Height = 17
      Caption = '&Content'
      TabOrder = 2
      OnClick = KindEditChange
    end
    object KindDOSAttrEdit: TUiRadioButton
      Left = 8
      Top = 88
      Height = 17
      Caption = '&DOS attribute'
      TabOrder = 3
      OnClick = KindEditChange
    end
    object KindUnixFileTypeEdit: TUiRadioButton
      Left = 8
      Top = 109
      Height = 17
      Caption = '&Unix file type'
      TabOrder = 4
      OnClick = KindEditChange
    end
    object KindVcsStatusEdit: TUiRadioButton
      Left = 8
      Top = 130
      Height = 17
      Caption = '&Version control status'
      TabOrder = 5
      OnClick = KindEditChange
    end
  end
  object PanelView: TUiActivePanelView
    Left = 180
    Top = 0
    Width = 354
    Height = 205
    TabOrder = 1
    object DatePanel: TUiActivePanel
      object DateSubPanel: TUiPanel
        Left = 0
        Top = 0
        Width = 354
        Height = 50
        BevelOuter = bvNone
        TabOrder = 0
        object DateSubLbl: TUiLabel
          Left = 8
          Top = 8
          Height = 13
          Caption = 'Exclude files:'
        end
        object DateTopBevel: TUiBevel
          Left = 8
          Top = 48
          Width = 338
          Height = 2
          Shape = bsTopLine
        end
        object DateOlderEdit: TUiRadioButton
          Left = 8
          Top = 25
          Height = 17
          Caption = '&Older than'
          TabOrder = 0
          OnClick = SomethingChangedClick
        end
        object DateNewerEdit: TUiRadioButton
          Left = 177
          Top = 25
          Height = 17
          Caption = '&Newer than'
          TabOrder = 1
          OnClick = SomethingChangedClick
        end
      end
      object DateUseDaysEdit: TUiCheckBox
        Left = 8
        Top = 58
        Height = 17
        Caption = 'Da&y(s) ago'
        TabOrder = 1
        OnClick = SomethingChangedClick
      end
      object DateDaysEdit: TUiSpinEdit
        Left = 8
        Top = 83
        Width = 49
        Height = 21
        Max = 9999
        MaxLength = 4
        TabOrder = 2
        OnChange = SomethingChangedClick
      end
      object DateDateEdit: TUiDateTimePicker
        Left = 8
        Top = 83
        Width = 101
        Height = 21
        TabOrder = 3
        OnChange = SomethingChangedClick
      end
      object DateTimeEdit: TUiDateTimePicker
        Left = 117
        Top = 83
        Width = 101
        Height = 21
        Kind = dtkTime
        TabOrder = 4
        OnChange = SomethingChangedClick
      end
    end
    object SizePanel: TUiActivePanel
      object SizeSubPanel: TUiPanel
        Left = 0
        Top = 0
        Width = 354
        Height = 50
        BevelOuter = bvNone
        TabOrder = 0
        object SizeSubLbl: TUiLabel
          Left = 8
          Top = 8
          Height = 13
          Caption = 'Exclude files:'
        end
        object SizeSmallerEdit: TUiRadioButton
          Left = 8
          Top = 25
          Height = 17
          Caption = 'Small&er than'
          TabOrder = 0
          OnClick = SomethingChangedClick
        end
        object SizeLargerEdit: TUiRadioButton
          Left = 177
          Top = 25
          Height = 17
          Caption = '&Larger than'
          TabOrder = 1
          OnClick = SomethingChangedClick
        end
      end
      object SizeEdit: TUiSpinEdit
        Left = 8
        Top = 50
        Width = 89
        Height = 21
        TabOrder = 1
        OnChange = SomethingChangedClick
      end
      object SizeUnitEdit: TUiComboBox
        Left = 101
        Top = 50
        Width = 67
        Height = 21
        Style = csDropDownList
        TabOrder = 2
        OnChange = SomethingChangedClick
      end
    end
    object ContentPanel: TUiActivePanel
      object ContentFindREBtn: TUiSpeedButton
        Left = 323
        Top = 50
        Hint = 'Insert Regular Expression Element'
        DropDown = True
        Flat = False
        PopupMenu = ContentFindREPopup
      end
      object ContentSubPanel: TUiPanel
        Left = 0
        Top = 0
        Width = 354
        Height = 50
        BevelOuter = bvNone
        TabOrder = 0
        object ContentSubLbl: TUiLabel
          Left = 8
          Top = 8
          Height = 13
          Caption = 'Exclude files:'
        end
        object ContentSubEdit: TUiRadioButton
          Left = 8
          Top = 25
          Height = 17
          Caption = 'C&ontaining'
          TabOrder = 0
          OnClick = SomethingChangedClick
        end
        object ContentSubNonEdit: TUiRadioButton
          Left = 177
          Top = 25
          Height = 17
          Caption = '&Not containing'
          TabOrder = 1
          OnClick = SomethingChangedClick
        end
      end
      object ContentFindStrEdit: TUiEdit
        Left = 8
        Top = 50
        Width = 307
        Height = 21
        TabOrder = 1
        OnChange = SomethingChangedClick
      end
      object ContentCaseSensitiveEdit: TUiCheckBox
        Left = 8
        Top = 79
        Height = 17
        Caption = 'Match character cas&e'
        TabOrder = 2
        OnClick = SomethingChangedClick
      end
      object ContentWholeWordsEdit: TUiCheckBox
        Left = 8
        Top = 100
        Height = 17
        Caption = '&Whole words only'
        TabOrder = 3
        OnClick = SomethingChangedClick
      end
      object ContentIsRegExpEdit: TUiCheckBox
        Left = 8
        Top = 121
        Height = 17
        Caption = 'Regular e&xpression'
        TabOrder = 4
        OnClick = SomethingChangedClick
      end
      object ContentREHelpBtn: TUiButton
        Left = 24
        Top = 142
        HelpType = htKeyword
        HelpKeyword = 'Sample_Regular_Expressions'
        Caption = 'RE Exam&ples'
        TabOrder = 5
        AutoSize = asLeft
      end
    end
    object DOSAttrPanel: TUiActivePanel
      object DOSAttrSubPanel: TUiPanel
        Left = 0
        Top = 0
        Width = 354
        Height = 50
        BevelOuter = bvNone
        TabOrder = 0
        object DOSAttrSubLbl: TUiLabel
          Left = 8
          Top = 8
          Height = 13
          Caption = 'Exclude files if DOS attribute:'
        end
        object DOSAttrTopBevel: TUiBevel
          Left = 8
          Top = 48
          Width = 338
          Height = 2
          Shape = bsTopLine
        end
        object DOSAttrSubEdit: TUiRadioButton
          Left = 8
          Top = 25
          Height = 17
          Caption = '&Is set'
          TabOrder = 0
          OnClick = SomethingChangedClick
        end
        object DOSAttrSubNonEdit: TUiRadioButton
          Left = 177
          Top = 25
          Height = 17
          Caption = 'Is &not set'
          TabOrder = 1
          OnClick = SomethingChangedClick
        end
      end
      object DOSAttrGridPanel: TUiGridPanel
        Left = 8
        Top = 58
        Width = 338
        Height = 147
        BevelOuter = bvNone
        ColumnCollection = <
          item
            Value = 0
          end
          item
            Value = 0
          end
        >
        ControlCollection = <
        >
        RowCollection = <
          item
            Value = 0.491943359375
          end
          item
            Value = 0.491943359375
          end
          item
            Value = 0.491943359375
          end
          item
            Value = 0.491943359375
          end
          item
            Value = 0.491943359375
          end
          item
            Value = 0.491943359375
          end
          item
            Value = -0.14892578125
          end
        >
        TabOrder = 1
      end
    end
    object UnixFileTypePanel: TUiActivePanel
      object UnixFileTypeSubPanel: TUiPanel
        Left = 0
        Top = 0
        Width = 354
        Height = 50
        BevelOuter = bvNone
        TabOrder = 0
        object UnixFileTypeSubLbl: TUiLabel
          Left = 8
          Top = 8
          Height = 13
          Caption = 'Exclude files if Unix file type:'
        end
        object UnixFileTypeTopBevel: TUiBevel
          Left = 8
          Top = 48
          Width = 338
          Height = 2
          Shape = bsTopLine
        end
        object UnixFileTypeSubEdit: TUiRadioButton
          Left = 8
          Top = 25
          Height = 17
          Caption = '&Is'
          TabOrder = 0
          OnClick = SomethingChangedClick
        end
        object UnixFileTypeSubNonEdit: TUiRadioButton
          Left = 177
          Top = 25
          Height = 17
          Caption = 'Is &not'
          TabOrder = 1
          OnClick = SomethingChangedClick
        end
      end
      object UnixFileTypeListPanel: TUiPanel
        Left = 8
        Top = 58
        Width = 338
        Height = 147
        BevelOuter = bvNone
        TabOrder = 1
      end
    end
    object VcsStatusPanel: TUiActivePanel
      object VcsStatusSubPanel: TUiPanel
        Left = 0
        Top = 0
        Width = 354
        Height = 50
        BevelOuter = bvNone
        TabOrder = 0
        object VcsStatusSubLbl: TUiLabel
          Left = 8
          Top = 8
          Height = 13
          Caption = 'Exclude files if version control status:'
        end
        object VcsStatusTopBevel: TUiBevel
          Left = 8
          Top = 48
          Width = 338
          Height = 2
          Shape = bsTopLine
        end
        object VcsStatusSubEdit: TUiRadioButton
          Left = 8
          Top = 25
          Height = 17
          Caption = '&Is set'
          TabOrder = 0
          OnClick = SomethingChangedClick
        end
        object VcsStatusSubNonEdit: TUiRadioButton
          Left = 177
          Top = 25
          Height = 17
          Caption = 'Is &not set'
          TabOrder = 1
          OnClick = SomethingChangedClick
        end
      end
      object VcsStatusListPanel: TUiPanel
        Left = 8
        Top = 58
        Width = 338
        Height = 147
        BevelOuter = bvNone
        TabOrder = 1
      end
    end
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 205
    Width = 536
    TabOrder = 2
    object OkBtn: TUiOkBtn
    end
    object CancelBtn: TUiCancelBtn
    end
  end
  object ContentFindREPopup: TUiPopupMenu
    Left = 500
    Top = 8
    object TabItem: TUiMenuItem
      Caption = 'Tab Character (\t)'
      OnClick = ContentFindREItemClick
    end
    object AnyItem: TUiMenuItem
      Caption = 'Any Character (.)'
      OnClick = ContentFindREItemClick
    end
    object AlphaItem: TUiMenuItem
      Caption = 'Any Alphanumeric Character (\w)'
      OnClick = ContentFindREItemClick
    end
    object NonAlphaItem: TUiMenuItem
      Caption = 'Any Non-alphanumeric Character (\W)'
      OnClick = ContentFindREItemClick
    end
    object NumItem: TUiMenuItem
      Caption = 'Any Numeric Character (\d)'
      OnClick = ContentFindREItemClick
    end
    object NonNumItem: TUiMenuItem
      Caption = 'Any Non-numeric Character (\D)'
      OnClick = ContentFindREItemClick
    end
    object WSItem: TUiMenuItem
      Caption = 'Any Whitespace Character (\s)'
      OnClick = ContentFindREItemClick
    end
    object CharSetItem: TUiMenuItem
      Caption = 'Character in Set ([])'
      OnClick = ContentFindREItemClick
    end
    object NotCharSetItem: TUiMenuItem
      Caption = 'Character Not in Set ([^])'
      OnClick = ContentFindREItemClick
    end
    object BeginItem: TUiMenuItem
      Caption = 'Beginning of Line (^)'
      OnClick = ContentFindREItemClick
    end
    object EndItem: TUiMenuItem
      Caption = 'End of Line ($)'
      OnClick = ContentFindREItemClick
    end
    object TaggedItem: TUiMenuItem
      Caption = 'Tagged Expression (())'
      OnClick = ContentFindREItemClick
    end
    object OrItem: TUiMenuItem
      Caption = 'Or (|)'
      OnClick = ContentFindREItemClick
    end
    object ZeroOrMoreItem: TUiMenuItem
      Caption = '0 Or More Matches (*)'
      OnClick = ContentFindREItemClick
    end
    object OneOrMoreItem: TUiMenuItem
      Caption = '1 Or More Matches (+)'
      OnClick = ContentFindREItemClick
    end
    object ZeroOrOneItem: TUiMenuItem
      Caption = '0 Or 1 Matches (?)'
      OnClick = ContentFindREItemClick
    end
  end
end
