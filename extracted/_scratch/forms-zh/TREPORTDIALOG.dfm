object ReportDialog: TReportDialog
  HelpType = htKeyword
  HelpKeyword = 'DlgReport'
  BorderIcons = [biSystemMenu, biHelp]
  Caption = '%'
  ClientHeight = 394
  ClientWidth = 585
  OnCreate = FormCreate
  OnDestroy = FormDestroy
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object LayoutLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = 'Report la&yout:'
    FocusControl = LayoutListBox
  end
  object OptionsLbl: TUiLabel
    Left = 192
    Top = 8
    Height = 13
    Caption = 'Report options:'
  end
  object OutputBevel: TUiBevel
    Left = 8
    Top = 154
    Width = 569
    Height = 1
    Shape = bsTopLine
  end
  object LayoutListBox: TUiListBox
    Left = 8
    Top = 25
    Width = 176
    Height = 121
    Items.Strings = ('Side-by-side', 'Summary')
    TabOrder = 0
    OnClick = SomethingChangedClick
  end
  object OptionsPanel: TUiPanel
    Left = 192
    Top = 25
    Width = 385
    Height = 121
    BevelOuter = bvNone
    TabOrder = 1
    object BasicPanel: TUiPanel
      Left = 0
      Top = 0
      Width = 385
      Height = 46
      Align = alTop
      BevelOuter = bvNone
      TabOrder = 0
      object SelOnlyEdit: TUiCheckBox
        Left = 0
        Top = 2
        Height = 17
        Caption = 'Just &selection'
        TabOrder = 0
        OnClick = SomethingChangedClick
      end
      object InsigIgnoredEdit: TUiCheckBox
        Left = 0
        Top = 23
        Height = 17
        Caption = 'Ignore &unimportant'
        TabOrder = 1
        OnClick = SomethingChangedClick
      end
    end
    object DisplayFilterPanel: TUiPanel
      Left = 0
      Top = 46
      Width = 385
      Height = 29
      Align = alTop
      BevelOuter = bvNone
      TabOrder = 1
      object DisplayFilterEdit: TUiComboBox
        Left = 0
        Top = 2
        Width = 185
        Height = 21
        Style = csDropDownList
        TabOrder = 0
        OnChange = SomethingChangedClick
      end
    end
    object LayoutPanelView: TUiActivePanelView
      Left = 0
      Top = 75
      Width = 385
      Height = 46
      Align = alClient
      TabOrder = 2
      object SideBySidePanel: TUiActivePanel
        object IncludeNumsEdit: TUiCheckBox
          Left = 0
          Top = 2
          Height = 17
          Caption = 'Include &numbers'
          TabOrder = 0
          OnClick = SomethingChangedClick
        end
      end
    end
  end
  object OutputPanel: TUiPanel
    Left = 8
    Top = 162
    Width = 401
    Height = 193
    BevelOuter = bvNone
    TabOrder = 2
    object TitleLbl: TUiLabel
      Left = 0
      Top = 155
      Height = 13
      Caption = 'Report t&itle:'
      FocusControl = TitleEdit
    end
    object OutputLbl: TUiLabel
      Left = 0
      Top = 0
      Height = 13
      Caption = 'Output options:'
    end
    object PrintEdit: TUiRadioButton
      Left = 0
      Top = 17
      Height = 17
      Caption = 'P&rinter'
      TabOrder = 0
      OnClick = SomethingChangedClick
    end
    object HTMLEdit: TUiRadioButton
      Left = 0
      Top = 38
      Height = 17
      Caption = '&HTML report'
      TabOrder = 1
      OnClick = SomethingChangedClick
    end
    object PlainTextEdit: TUiRadioButton
      Left = 0
      Top = 59
      Height = 17
      Caption = 'Plain &text'
      TabOrder = 2
      OnClick = SomethingChangedClick
    end
    object OutputPanelView: TUiActivePanelView
      Left = 124
      Top = 0
      Width = 277
      Height = 130
      TabOrder = 3
      object PrintPanel: TUiActivePanel
        object PrintStyleKindPanel: TUiPanel
          Left = 0
          Top = 0
          Width = 277
          Height = 46
          Align = alTop
          BevelOuter = bvNone
          TabOrder = 0
          object PrintStyleKindLbl: TUiLabel
            Left = 0
            Top = 0
            Height = 13
            Caption = 'Difference high&lighting:'
            FocusControl = PrintStyleKindEdit
          end
          object PrintStyleKindEdit: TUiComboBox
            Left = 0
            Top = 17
            Width = 94
            Height = 21
            Style = csDropDownList
            TabOrder = 0
            OnChange = SomethingChangedClick
            Items.Strings = ('Use color', 'Monochrome')
          end
        end
        object PrintWrapModePanel: TUiPanel
          Left = 0
          Top = 46
          Width = 277
          Height = 84
          Align = alTop
          BevelOuter = bvNone
          TabOrder = 1
          object PrintWrapModeLbl: TUiLabel
            Left = 0
            Top = 0
            Height = 13
            Caption = 'Wrap lines:'
          end
          object PrintWrapNoneEdit: TUiRadioButton
            Left = 0
            Top = 17
            Height = 17
            Caption = 'N&o wrap'
            TabOrder = 0
            OnClick = SomethingChangedClick
          end
          object PrintWrapWordEdit: TUiRadioButton
            Left = 0
            Top = 38
            Height = 17
            Caption = 'Wrap wor&ds'
            TabOrder = 1
            OnClick = SomethingChangedClick
          end
          object PrintWrapCharEdit: TUiRadioButton
            Left = 0
            Top = 59
            Height = 17
            Caption = '&Wrap characters'
            TabOrder = 2
            OnClick = SomethingChangedClick
          end
        end
      end
      object HTMLPanel: TUiActivePanel
        object HTMLStylePanel: TUiPanel
          Left = 0
          Top = 0
          Width = 277
          Height = 92
          Align = alTop
          BevelOuter = bvNone
          TabOrder = 0
          object HTMLStyleKindLbl: TUiLabel
            Left = 0
            Top = 0
            Height = 13
            Caption = 'Difference high&lighting:'
            FocusControl = HTMLStyleKindEdit
          end
          object HTMLStyleURLLbl: TUiLabel
            Left = 16
            Top = 46
            Height = 13
            Caption = 'Custo&m stylesheet URL:'
            FocusControl = HTMLStyleURLEdit
          end
          object HTMLStyleKindEdit: TUiComboBox
            Left = 0
            Top = 17
            Width = 229
            Height = 21
            Style = csDropDownList
            TabOrder = 0
            OnChange = SomethingChangedClick
            Items.Strings = ('Use color stylesheet (embedded)', 'Use monochrome stylesheet (embedded)', 'Use custom stylesheet (external)')
          end
          object HTMLStyleURLEdit: TUiEdit
            Left = 16
            Top = 63
            Width = 261
            Height = 21
            TabOrder = 1
            OnChange = SomethingChangedClick
          end
        end
        object HTMLWrapEdit: TUiCheckBox
          Left = 0
          Top = 92
          Height = 17
          Caption = 'Allow word &wrapping'
          TabOrder = 1
          OnClick = SomethingChangedClick
        end
      end
    end
    object TitleEdit: TUiEdit
      Left = 0
      Top = 172
      Width = 401
      Height = 21
      TabOrder = 4
      OnChange = SomethingChangedClick
    end
  end
  object BtnPanelView: TUiActivePanelView
    Left = 417
    Top = 270
    Width = 160
    Height = 85
    TabOrder = 3
    object BtnPrintPanel: TUiActivePanel
      object PreviewBtn: TUiButton
        Left = 0
        Top = 0
        Width = 160
        Caption = 'Print Pre&view'
        TabOrder = 0
        OnClick = PreviewClick
      end
      object SetupBtn: TUiButton
        Left = 0
        Top = 31
        Width = 160
        Caption = 'Pa&ge Setup...'
        TabOrder = 1
        OnClick = SetupClick
      end
      object PrintBtn: TUiButton
        Left = 0
        Top = 62
        Width = 160
        Caption = '&Print...'
        Default = True
        TabOrder = 2
        OnClick = PrintClick
      end
    end
    object BtnFilePanel: TUiActivePanel
      object WebBrowserBtn: TUiButton
        Left = 0
        Top = 0
        Width = 160
        Caption = '&View in Browser'
        TabOrder = 0
        OnClick = WebBrowserClick
      end
      object CopyToClipboardBtn: TUiButton
        Left = 0
        Top = 31
        Width = 160
        Caption = '&Copy to Clipboard'
        TabOrder = 1
        OnClick = CopyToClipboardClick
      end
      object SaveBtn: TUiButton
        Left = 0
        Top = 62
        Width = 160
        Caption = 'Save &As...'
        Default = True
        TabOrder = 2
        OnClick = SaveClick
      end
    end
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 355
    Width = 585
    TabOrder = 4
    object CloseBtn: TUiCloseBtn
    end
  end
end
