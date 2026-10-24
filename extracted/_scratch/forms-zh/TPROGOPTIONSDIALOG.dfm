object ProgOptionsDialog: TProgOptionsDialog
  HelpType = htKeyword
  BorderIcons = [biSystemMenu, biHelp]
  Caption = 'Options'
  ClientHeight = 501
  ClientWidth = 657
  OnActivate = FormActivate
  OnClose = FormClose
  OnCreate = FormCreate
  OnDestroy = FormDestroy
  OnShortCut = FormShortCut
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object LeftBevel: TUiBevel
    Left = 185
    Top = 0
    Width = 4
    Height = 462
    Align = alLeft
    Shape = bsSpacer
  end
  object CategoryPanel: TUiPanel
    Left = 0
    Top = 0
    Width = 185
    Height = 462
    Align = alLeft
    BevelOuter = bvNone
    Color = 15591395
    ParentBackground = False
    TabOrder = 0
    StyleElements = [seFont, seBorder]
    OnPaint = CategoryPanelPaint
    object CategorySearchBevel: TUiBevel
      Left = 0
      Top = 0
      Width = 185
      Height = 41
      Shape = bsSpacer
    end
    object CategorySearchEdit: TUiSearchEdit
      Left = 8
      Top = 8
      Width = 169
      Height = 21
      TabOrder = 0
      OnChange = CategorySearchEditChange
    end
  end
  object PanelView: TUiActivePanelView
    Left = 189
    Top = 0
    Width = 468
    Height = 462
    Align = alClient
    TabOrder = 1
    object StartupPanel: TUiActivePanel
      HelpType = htKeyword
      HelpKeyword = 'OptionsStartup'
      object StartupLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 22
        Caption = 'Startup'
        FontColor = clGrayText
        FontSize = 3
        UseTitleFont = True
      end
      object WorkspaceAutoLoadNameLbl: TUiLabel
        Left = 8
        Top = 34
        Height = 13
        Caption = 'Load &workspace:'
        FocusControl = WorkspaceAutoLoadNameEdit
      end
      object WorkspaceAutoSaveNameLbl: TUiLabel
        Left = 238
        Top = 34
        Height = 13
        Caption = 'On exit, sa&ve workspace as:'
        FocusControl = WorkspaceAutoSaveNameEdit
      end
      object WorkspaceAutoLoadNameEdit: TUiComboBox
        Left = 8
        Top = 51
        Width = 222
        Height = 21
        TabOrder = 0
        OnChange = SomethingChangedClick
      end
      object WorkspaceAutoSaveNameEdit: TUiComboBox
        Left = 238
        Top = 51
        Width = 222
        Height = 21
        TabOrder = 1
        OnChange = SomethingChangedClick
      end
      object QuickCompareShowEdit: TUiCheckBox
        Left = 8
        Top = 80
        Height = 17
        Caption = 'When starting with file comparison, show &quick compare dialog'
        TabOrder = 2
        OnClick = SomethingChangedClick
      end
      object QuickCompareRulesBasedPanel: TUiPanel
        Left = 16
        Top = 99
        Width = 444
        Height = 42
        BevelOuter = bvNone
        TabOrder = 3
        object QuickCompareBinaryEdit: TUiRadioButton
          Left = 8
          Top = 2
          Height = 17
          Caption = 'B&inary quick compare'
          TabOrder = 0
          OnClick = SomethingChangedClick
        end
        object QuickCompareRulesBasedEdit: TUiRadioButton
          Left = 8
          Top = 23
          Height = 17
          Caption = '&Rules-based quick compare'
          TabOrder = 1
          OnClick = SomethingChangedClick
        end
      end
      object QuickCompareSkipDiffEdit: TUiCheckBox
        Left = 24
        Top = 143
        Height = 17
        Caption = '&Open view automatically if files are different'
        TabOrder = 4
        OnClick = SomethingChangedClick
      end
      object ClipboardPanel: TUiPanel
        Left = 0
        Top = 176
        Width = 468
        Height = 67
        BevelOuter = bvNone
        TabOrder = 5
        object ClipboardBevel: TUiBevel
          Left = 8
          Top = 0
          Width = 452
          Height = 1
          Shape = bsTopLine
        end
        object ClipboardLbl: TUiLabel
          Left = 8
          Top = 8
          Height = 22
          Caption = 'Clipboard Compare'
          FontColor = clGrayText
          FontSize = 3
          UseTitleFont = True
        end
        object ClipboardEdit: TUiCheckBox
          Left = 8
          Top = 34
          Height = 17
          Caption = 'Run &Clipboard Compare on Windows startup'
          TabOrder = 0
          OnClick = SomethingChangedClick
        end
      end
      object ShellExtPanel: TUiPanel
        Left = 0
        Top = 243
        Width = 468
        Height = 236
        BevelOuter = bvNone
        TabOrder = 6
        object ShellExtBevel: TUiBevel
          Left = 8
          Top = 0
          Width = 452
          Height = 1
          Shape = bsTopLine
        end
        object ShellExtLbl: TUiLabel
          Left = 8
          Top = 8
          Height = 22
          Caption = 'Explorer Integration'
          FontColor = clGrayText
          FontSize = 3
          UseTitleFont = True
        end
        object ShellExtMissingLbl: TUiLabel
          Left = 8
          Top = 34
          Width = 452
          Height = 26
          Caption = 'This is a portable install.  Explorer integration requires installation of Beyond Compare for all users or for current user.'
          WordWrap = True
          FontStyle = [fsBold]
        end
        object ShellExtEdit: TUiCheckBox
          Left = 8
          Top = 73
          Height = 17
          Caption = 'Include Beyond Compare in &Explorer context menu'
          TabOrder = 0
          OnClick = SomethingChangedClick
        end
        object ShellExtItemPosTable: TUiListTable
          Left = 24
          Top = 94
          Width = 280
          Height = 101
          Cols.Data = ('', '120')
          Cols.Strings = ('Command', 'Location')
          ModifyColIndex = 1
          TabOrder = 1
          VertLines = True
          OnModifyApply = SomethingChangedClick
          OnModifyInit = ShellExtItemPosTableModifyInit
        end
        object ShellExtHideSelLeftEdit: TUiCheckBox
          Left = 24
          Top = 203
          Height = 17
          Caption = 'Hide "Select Left" if there is already a saved selection'
          TabOrder = 2
          OnClick = SomethingChangedClick
        end
      end
    end
    object TabPanel: TUiActivePanel
      HelpType = htKeyword
      HelpKeyword = 'OptionsTab'
      object TabLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 22
        Caption = 'Tabs'
        FontColor = clGrayText
        FontSize = 3
        UseTitleFont = True
      end
      object TabTabStopsLinkLbl: TUiLinkLabel
        Left = 8
        Top = 294
        Width = 452
        Height = 13
        Caption = 'For settings that control tab stops in text files, see <a href="">%s</a>'
        LinkFontColor = clWindowText
        LinkFontStyle = [fsBold]
        WordWrap = True
      end
      object ViewNewTabLbl: TUiLabel
        Left = 8
        Top = 34
        Height = 13
        Caption = 'Open sessions in:'
      end
      object ChildViewNewTabLbl: TUiLabel
        Left = 8
        Top = 97
        Height = 13
        Caption = 'Open child sessions in:'
      end
      object ViewNewTabPanel: TUiPanel
        Left = 0
        Top = 49
        Width = 468
        Height = 42
        BevelOuter = bvNone
        TabOrder = 0
        object ViewNewWindowEdit: TUiRadioButton
          Left = 8
          Top = 2
          Height = 17
          Caption = 'A new win&dow'
          TabOrder = 0
          OnClick = SomethingChangedClick
        end
        object ViewNewTabEdit: TUiRadioButton
          Left = 8
          Top = 23
          Height = 17
          Caption = 'A new &tab'
          TabOrder = 1
          OnClick = SomethingChangedClick
        end
      end
      object ChildViewNewTabPanel: TUiPanel
        Left = 0
        Top = 112
        Width = 468
        Height = 42
        BevelOuter = bvNone
        TabOrder = 1
        object ChildViewNewWindowEdit: TUiRadioButton
          Left = 8
          Top = 2
          Height = 17
          Caption = 'A new wind&ow'
          TabOrder = 0
          OnClick = SomethingChangedClick
        end
        object ChildViewNewTabEdit: TUiRadioButton
          Left = 8
          Top = 23
          Height = 17
          Caption = 'A new ta&b'
          TabOrder = 1
          OnClick = SomethingChangedClick
        end
      end
      object TabNewNextEdit: TUiCheckBox
        Left = 8
        Top = 160
        Height = 17
        Caption = 'Open &new tab next to active tab'
        TabOrder = 2
        OnClick = SomethingChangedClick
      end
      object TabSingleCloseWindowEdit: TUiCheckBox
        Left = 8
        Top = 181
        Height = 17
        Caption = 'Closing &last remaining tab closes the window'
        TabOrder = 3
        OnClick = SomethingChangedClick
      end
      object TabsConfirmCloseEdit: TUiCheckBox
        Left = 8
        Top = 202
        Height = 17
        Caption = '&Warn when closing multiple tabs'
        TabOrder = 4
        OnClick = SomethingChangedClick
      end
      object WindowsConfirmCloseEdit: TUiCheckBox
        Left = 8
        Top = 223
        Height = 17
        Caption = 'Wa&rn when closing multiple windows'
        TabOrder = 5
        OnClick = SomethingChangedClick
      end
      object TabSingleHideEdit: TUiCheckBox
        Left = 8
        Top = 244
        Height = 17
        Caption = '&Hide tab bar if single tab'
        TabOrder = 6
        OnClick = SomethingChangedClick
      end
      object TabsOnTaskbarEdit: TUiCheckBox
        Left = 8
        Top = 265
        Height = 17
        Caption = 'Show &previews for individual tabs in the taskbar'
        TabOrder = 7
        OnClick = SomethingChangedClick
      end
    end
    object ColorPanel: TUiActivePanel
      object ColorLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 22
        Caption = 'Theme, Colors, Fonts'
        FontColor = clGrayText
        FontSize = 3
        UseTitleFont = True
      end
      object ColorLinkLbl: TUiLinkLabel
        Left = 8
        Top = 441
        Height = 13
        Caption = 'Additional color schemes available on <a href="%s">Scooter Software''s web site</a>.'
      end
      object HighContrastLbl: TUiLabel
        Left = 169
        Top = 34
        Width = 291
        Height = 46
        AutoSize = False
        Caption = 'Windows high contrast mode takes priority over selected appearance'
        Visible = False
        WordWrap = True
      end
      object ThemeModeEdit: TUiComboBox
        Left = 8
        Top = 34
        Width = 145
        Height = 21
        Style = csDropDownList
        TabOrder = 0
        OnChange = ThemeModeEditChange
      end
      object PreviewEdit: TUiCheckBox
        Left = 8
        Top = 63
        Height = 17
        Caption = '&Preview'
        TabOrder = 1
        OnClick = PreviewClick
      end
      object ColorPageControl: TUiPageControl
        Left = 0
        Top = 88
        Width = 468
        Height = 345
        ActivePage = DirColorTabSheet
        TabOrder = 2
        object DirColorTabSheet: TUiTabSheet
          HelpType = htKeyword
          HelpKeyword = 'OptionsDirColor'
          Caption = 'Folder Views'
          OnShow = ColorTabSheetShow
          object DirFGColorLbl: TUiLabel
            Left = 260
            Top = 8
            Height = 13
            Caption = '&Text color:'
            FocusControl = DirFGColorEdit
          end
          object DirBGColorLbl: TUiLabel
            Left = 260
            Top = 54
            Height = 13
            Caption = 'Bac&kground:'
            FocusControl = DirBGColorEdit
          end
          object DirFolderInfoFGColorLbl: TUiLabel
            Left = 260
            Top = 100
            Height = 13
            Caption = 'F&older info:'
            FocusControl = DirFolderInfoFGColorEdit
          end
          object DirLogColorLbl: TUiLabel
            Left = 260
            Top = 8
            Height = 13
            Caption = 'Bac&kground:'
            FocusControl = DirLogColorEdit
          end
          object DirSelUnfocusedBGColorLbl: TUiLabel
            Left = 260
            Top = 100
            Height = 13
            Caption = '&Inactive background:'
            FocusControl = DirSelUnfocusedBGColorEdit
          end
          object DirFontLbl: TUiLabel
            Left = 89
            Top = 236
            Width = 363
            Height = 13
            AutoSize = False
            Caption = 'Sample Text'
          end
          object DirElementTreeView: TUiTreeView
            Left = 8
            Top = 8
            Width = 244
            Height = 194
            ReadOnly = True
            TabOrder = 0
            OnChange = DirElementTreeViewChange
          end
          object DirFGColorEdit: TUiColorEdit
            Left = 260
            Top = 25
            Width = 192
            Height = 21
            TabOrder = 1
            OnSelect = DirElementEditChange
          end
          object DirBGColorEdit: TUiColorEdit
            Left = 260
            Top = 71
            Width = 192
            Height = 21
            TabOrder = 2
            OnSelect = DirElementEditChange
          end
          object DirFolderInfoFGColorEdit: TUiColorEdit
            Left = 260
            Top = 117
            Width = 192
            Height = 21
            AllowDefault = False
            Selected = clBlack
            TabOrder = 3
            OnSelect = DirElementEditChange
          end
          object DirUseStripesEdit: TUiCheckBox
            Left = 260
            Top = 146
            Height = 17
            Caption = 'Use st&ripes'
            TabOrder = 4
            OnClick = SomethingChangedClick
          end
          object DirStripeBGColorEdit: TUiColorEdit
            Left = 260
            Top = 167
            Width = 192
            Height = 21
            AllowDefault = False
            Selected = clBlack
            TabOrder = 5
            OnSelect = DirElementEditChange
          end
          object DirLogColorEdit: TUiColorEdit
            Left = 260
            Top = 25
            Width = 192
            Height = 21
            AllowDefault = False
            Selected = clBlack
            TabOrder = 6
            OnSelect = DirElementEditChange
          end
          object DirLogSystemEdit: TUiCheckBox
            Left = 260
            Top = 54
            Height = 17
            Caption = 'Use syste&m'
            TabOrder = 7
            OnClick = SomethingChangedClick
          end
          object DirSelUnfocusedBGColorEdit: TUiColorEdit
            Left = 260
            Top = 117
            Width = 192
            Height = 21
            AllowDefault = False
            Selected = clBlack
            TabOrder = 8
            OnSelect = DirElementEditChange
          end
          object DirSelSystemEdit: TUiCheckBox
            Left = 260
            Top = 146
            Height = 17
            Caption = 'Use syste&m'
            TabOrder = 9
            OnClick = SomethingChangedClick
          end
          object DirFontSystemEdit: TUiCheckBox
            Left = 8
            Top = 210
            Height = 17
            Caption = 'Use &system font'
            TabOrder = 10
            OnClick = SomethingChangedClick
          end
          object DirFontBtn: TUiButton
            Left = 8
            Top = 231
            Caption = '&Font...'
            TabOrder = 11
            OnClick = DirFontClick
            AutoSize = asLeft
          end
          object DirColoredFoldersEdit: TUiCheckBox
            Left = 8
            Top = 262
            Height = 17
            Caption = '&Color folders to reflect content'
            TabOrder = 12
            OnClick = SomethingChangedClick
          end
          object DirCenterGradientEdit: TUiCheckBox
            Left = 8
            Top = 283
            Height = 17
            Caption = 'Use &gradient for center background'
            TabOrder = 13
            OnClick = SomethingChangedClick
          end
        end
        object FileColorTabSheet: TUiTabSheet
          HelpType = htKeyword
          HelpKeyword = 'OptionsFileColor'
          Caption = 'File Views'
          OnShow = ColorTabSheetShow
          object FileFGColorLbl: TUiLabel
            Left = 260
            Top = 8
            Height = 13
            Caption = '&Text color:'
            FocusControl = FileFGColorEdit
          end
          object FileBGColorLbl: TUiLabel
            Left = 260
            Top = 54
            Height = 13
            Caption = 'Bac&kground:'
            FocusControl = FileBGColorEdit
          end
          object FileEditedColorLbl: TUiLabel
            Left = 260
            Top = 100
            Height = 13
            Caption = 'Ed&ited:'
            FocusControl = FileEditedColorEdit
          end
          object FileSavedColorLbl: TUiLabel
            Left = 360
            Top = 100
            Height = 13
            Caption = 'Sa&ved:'
            FocusControl = FileSavedColorEdit
          end
          object FileItemNumFontLbl: TUiLabel
            Left = 360
            Top = 146
            Width = 92
            Height = 23
            Alignment = taCenter
            AutoSize = False
            Caption = '123'
            Layout = tlCenter
          end
          object FileIgnoredColorLbl: TUiLabel
            Left = 260
            Top = 177
            Height = 13
            Caption = 'I&gnored section:'
            FocusControl = FileIgnoredColorEdit
          end
          object FileSelUnfocusedBGColorLbl: TUiLabel
            Left = 260
            Top = 100
            Height = 13
            Caption = '&Inactive background:'
            FocusControl = FileSelUnfocusedBGColorEdit
          end
          object FileFontStyleLbl: TUiLabel
            Left = 260
            Top = 100
            Height = 13
            Caption = '&Style:'
            FocusControl = FileFontStyleEdit
          end
          object FileDiffBGColorLbl: TUiLabel
            Left = 260
            Top = 147
            Height = 13
            Caption = 'Te&xt background:'
            FocusControl = FileDiffBGColorEdit
          end
          object FileHasSigBGColorLbl: TUiLabel
            Left = 260
            Top = 8
            Height = 13
            Caption = '&Important background:'
            FocusControl = FileHasSigBGColorEdit
          end
          object FileHasInsigBGColorLbl: TUiLabel
            Left = 260
            Top = 54
            Height = 13
            Caption = '&Unimportant background:'
            FocusControl = FileHasInsigBGColorEdit
          end
          object FileOutputBGColorLbl: TUiLabel
            Left = 260
            Top = 8
            Height = 13
            Caption = 'Ed&ited background:'
            FocusControl = FileOutputBGColorEdit
          end
          object FileEditorFontLbl: TUiLabel
            Left = 12
            Top = 249
            Width = 139
            Height = 13
            AutoSize = False
            Caption = 'Sample Text'
          end
          object FileListFontLbl: TUiLabel
            Left = 163
            Top = 249
            Width = 139
            Height = 13
            AutoSize = False
            Caption = 'Sample Text'
          end
          object FileHexFontLbl: TUiLabel
            Left = 314
            Top = 249
            Width = 139
            Height = 13
            AutoSize = False
            Caption = '89 FE DC BA'
          end
          object FileElementTreeView: TUiTreeView
            Left = 8
            Top = 8
            Width = 244
            Height = 194
            ReadOnly = True
            TabOrder = 0
            OnChange = FileElementTreeViewChange
          end
          object FileFGColorEdit: TUiColorEdit
            Left = 260
            Top = 25
            Width = 192
            Height = 21
            TabOrder = 1
            OnSelect = FileElementEditChange
          end
          object FileBGColorEdit: TUiColorEdit
            Left = 260
            Top = 71
            Width = 192
            Height = 21
            TabOrder = 2
            OnSelect = FileElementEditChange
          end
          object FileUseStripesEdit: TUiCheckBox
            Left = 260
            Top = 100
            Height = 17
            Caption = 'Use st&ripes'
            TabOrder = 3
            OnClick = SomethingChangedClick
          end
          object FileStripeBGColorEdit: TUiColorEdit
            Left = 260
            Top = 121
            Width = 192
            Height = 21
            AllowDefault = False
            Selected = clBlack
            TabOrder = 4
            OnSelect = FileElementEditChange
          end
          object FileEditedColorEdit: TUiColorEdit
            Left = 260
            Top = 117
            Width = 92
            Height = 21
            AllowDefault = False
            Selected = clBlack
            TabOrder = 5
            OnSelect = FileElementEditChange
          end
          object FileSavedColorEdit: TUiColorEdit
            Left = 360
            Top = 117
            Width = 92
            Height = 21
            AllowDefault = False
            Selected = clBlack
            TabOrder = 6
            OnSelect = FileElementEditChange
          end
          object FileItemNumFontBtn: TUiButton
            Left = 260
            Top = 146
            Caption = '&Font...'
            TabOrder = 7
            OnClick = FileItemNumFontClick
            AutoSize = asLeft
          end
          object FileIgnoredColorEdit: TUiColorEdit
            Left = 360
            Top = 177
            Width = 92
            Height = 21
            AllowDefault = False
            Selected = clBlack
            TabOrder = 8
            OnSelect = FileElementEditChange
          end
          object FileCurOverUnderOnlyEdit: TUiCheckBox
            Left = 260
            Top = 100
            Width = 193
            Height = 51
            Caption = 'Only in &over/under layout'
            TabOrder = 9
            WordWrap = True
            OnClick = SomethingChangedClick
            AutoSize = asNone
          end
          object FileSelUnfocusedBGColorEdit: TUiColorEdit
            Left = 260
            Top = 117
            Width = 192
            Height = 21
            AllowDefault = False
            Selected = clBlack
            TabOrder = 10
            OnSelect = FileElementEditChange
          end
          object FileSelSystemEdit: TUiCheckBox
            Left = 260
            Top = 146
            Height = 17
            Caption = 'Use syste&m'
            TabOrder = 11
            OnClick = SomethingChangedClick
          end
          object FileFontStyleEdit: TUiComboBox
            Left = 260
            Top = 117
            Width = 192
            Height = 22
            Style = csOwnerDrawFixed
            TabOrder = 12
            OnChange = FileElementEditChange
            OnDrawItem = FileFontStyleEditDrawItem
          end
          object FileDiffBGColorEdit: TUiColorEdit
            Left = 260
            Top = 164
            Width = 192
            Height = 21
            TabOrder = 13
            OnSelect = FileElementEditChange
          end
          object FileHasSigBGColorEdit: TUiColorEdit
            Left = 260
            Top = 25
            Width = 192
            Height = 21
            AllowDefault = False
            Selected = clBlack
            TabOrder = 14
            OnSelect = FileElementEditChange
          end
          object FileHasInsigBGColorEdit: TUiColorEdit
            Left = 260
            Top = 71
            Width = 192
            Height = 21
            AllowDefault = False
            Selected = clBlack
            TabOrder = 15
            OnSelect = FileElementEditChange
          end
          object FileOutputBGColorEdit: TUiColorEdit
            Left = 260
            Top = 25
            Width = 192
            Height = 21
            AllowDefault = False
            Selected = clBlack
            TabOrder = 16
            OnSelect = FileElementEditChange
          end
          object FileEditorFontBtn: TUiButton
            Left = 8
            Top = 218
            Caption = 'E&ditor Font...'
            TabOrder = 17
            OnClick = FileEditorFontClick
            AutoSize = asLeft
          end
          object FileListFontBtn: TUiButton
            Left = 159
            Top = 218
            Caption = '&Listing Font...'
            TabOrder = 18
            OnClick = FileListFontClick
            AutoSize = asLeft
          end
          object FileHexFontBtn: TUiButton
            Left = 310
            Top = 218
            Caption = '&Hex Font...'
            TabOrder = 19
            OnClick = FileHexFontClick
            AutoSize = asLeft
          end
        end
        object PixColorTabSheet: TUiTabSheet
          HelpType = htKeyword
          HelpKeyword = 'OptionsPixColor'
          Caption = 'Picture Compare'
          OnShow = ColorTabSheetShow
          object PixColorLbl: TUiLabel
            Left = 228
            Top = 8
            Height = 13
            Caption = 'Bac&kground:'
            FocusControl = PixColorEdit
          end
          object PixElementTreeView: TUiTreeView
            Left = 8
            Top = 8
            Width = 212
            Height = 194
            ReadOnly = True
            TabOrder = 0
            OnChange = PixElementTreeViewChange
          end
          object PixColorEdit: TUiColorEdit
            Left = 228
            Top = 25
            Width = 224
            Height = 21
            AllowDefault = False
            Selected = clBlack
            TabOrder = 1
            OnSelect = PixElementEditChange
          end
          object PixShowCheckerboardEdit: TUiCheckBox
            Left = 228
            Top = 54
            Height = 17
            Caption = 'Show &transparency as checkerboarding'
            TabOrder = 2
            OnClick = PixElementEditChange
          end
        end
      end
    end
    object TextPanel: TUiActivePanel
      HelpType = htKeyword
      HelpKeyword = 'OptionsText'
      object TextLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 22
        Caption = 'Text Editing'
        FontColor = clGrayText
        FontSize = 3
        UseTitleFont = True
      end
      object TextContextLinesLbl: TUiLabel
        Left = 8
        Top = 122
        Height = 13
        Caption = 'Number of &context lines:'
        FocusControl = TextContextLinesEdit
        Transparent = True
      end
      object TextTabStopsLinkLbl: TUiLinkLabel
        Left = 8
        Top = 172
        Height = 13
        Caption = 'To set tab stops, use <a href="">%s</a>'
        LinkFontColor = clWindowText
        LinkFontStyle = [fsBold]
      end
      object TextAutoIndentEdit: TUiCheckBox
        Left = 8
        Top = 34
        Height = 17
        Caption = 'Auto i&ndent'
        TabOrder = 0
        OnClick = SomethingChangedClick
      end
      object TextAutoUnindentEdit: TUiCheckBox
        Left = 8
        Top = 55
        Height = 17
        Caption = 'Bac&kspace unindents'
        TabOrder = 1
        OnClick = SomethingChangedClick
      end
      object TextFindCurWordEdit: TUiCheckBox
        Left = 8
        Top = 76
        Height = 17
        Caption = 'Initialize "Text to find" to be current &word'
        TabOrder = 2
        OnClick = SomethingChangedClick
      end
      object TextShowGapBarsEdit: TUiCheckBox
        Left = 8
        Top = 97
        Height = 17
        Caption = 'Show fi&ltered line counts'
        TabOrder = 3
        OnClick = SomethingChangedClick
      end
      object TextContextLinesEdit: TUiSpinEdit
        Left = 8
        Top = 139
        Width = 49
        Height = 21
        Max = 99
        MaxLength = 2
        TabOrder = 4
        OnChange = SomethingChangedClick
      end
    end
    object NextDiffPanel: TUiActivePanel
      HelpType = htKeyword
      HelpKeyword = 'OptionsNextDiff'
      object NextDiffLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 22
        Caption = 'Next Difference'
        FontColor = clGrayText
        FontSize = 3
        UseTitleFont = True
      end
      object NextDiffLoadFirstEdit: TUiCheckBox
        Left = 8
        Top = 34
        Height = 17
        Caption = 'When &loading new files, go to first difference'
        TabOrder = 0
        OnClick = SomethingChangedClick
      end
      object NextDiffAfterCopyEdit: TUiCheckBox
        Left = 8
        Top = 55
        Height = 17
        Caption = 'Go to next difference in files after &copying to other side'
        TabOrder = 1
        OnClick = SomethingChangedClick
      end
      object NextDiffFileSameDirEdit: TUiCheckBox
        Left = 8
        Top = 76
        Height = 17
        Caption = 'Limit "Next Difference Files" to current &folder'
        TabOrder = 2
        OnClick = SomethingChangedClick
      end
      object NextDiffNonePanel: TUiPanel
        Left = 0
        Top = 93
        Width = 468
        Height = 71
        BevelOuter = bvNone
        TabOrder = 3
        object NextDiffNoneLbl: TUiLabel
          Left = 8
          Top = 8
          Height = 13
          Caption = 'When no more differences:'
        end
        object NextDiffWrapEdit: TUiCheckBox
          Left = 8
          Top = 25
          Height = 17
          Caption = '&Wrap around to first difference'
          TabOrder = 0
          OnClick = SomethingChangedClick
        end
        object NextDiffShowMsgEdit: TUiCheckBox
          Left = 8
          Top = 46
          Height = 17
          Caption = 'Show &message panel'
          TabOrder = 1
          OnClick = SomethingChangedClick
        end
      end
    end
    object BackupPanel: TUiActivePanel
      HelpType = htKeyword
      HelpKeyword = 'OptionsBackup'
      object BackupLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 22
        Caption = 'Backups'
        FontColor = clGrayText
        FontSize = 3
        UseTitleFont = True
      end
      object BackupKindLbl: TUiLabel
        Left = 8
        Top = 80
        Height = 13
        Caption = 'Bac&k up "abc.txt" as:'
        FocusControl = BackupNameTildeExtEdit
      end
      object BackupOnCopyEdit: TUiCheckBox
        Left = 8
        Top = 34
        Height = 17
        Caption = 'Back up files before &copy'
        TabOrder = 0
        OnClick = SomethingChangedClick
      end
      object BackupOnSaveEdit: TUiCheckBox
        Left = 8
        Top = 55
        Height = 17
        Caption = 'Back up files before &save'
        TabOrder = 1
        OnClick = SomethingChangedClick
      end
      object BackupKindPanel: TUiPanel
        Left = 0
        Top = 95
        Width = 468
        Height = 63
        BevelOuter = bvNone
        TabOrder = 2
        object BackupNameTildeExtEdit: TUiRadioButton
          Left = 8
          Top = 2
          Height = 17
          Caption = '%'
          TabOrder = 0
          OnClick = SomethingChangedClick
        end
        object BackupNameExtTildeEdit: TUiRadioButton
          Left = 165
          Top = 2
          Height = 17
          Caption = '%'
          TabOrder = 1
          OnClick = SomethingChangedClick
        end
        object BackupNameExtBakEdit: TUiRadioButton
          Left = 322
          Top = 2
          Height = 17
          Caption = '%'
          TabOrder = 2
          OnClick = SomethingChangedClick
        end
        object BackupTildeNameExtEdit: TUiRadioButton
          Left = 8
          Top = 23
          Height = 17
          Caption = '%'
          TabOrder = 3
          OnClick = SomethingChangedClick
        end
        object BackupNameBakEdit: TUiRadioButton
          Left = 165
          Top = 23
          Height = 17
          Caption = '%'
          TabOrder = 4
          OnClick = SomethingChangedClick
        end
        object BackupNameBakExtEdit: TUiRadioButton
          Left = 322
          Top = 23
          Height = 17
          Caption = '%'
          TabOrder = 5
          OnClick = SomethingChangedClick
        end
        object BackupCopyToDirEdit: TUiRadioButton
          Left = 8
          Top = 44
          Height = 17
          Caption = 'abc.txt in this &folder:'
          TabOrder = 6
          OnClick = SomethingChangedClick
        end
      end
      object BackupDirEdit: TUiSpecBar
        Left = 24
        Top = 160
        Width = 436
        AutoCompleteEx = acDirs
        TabOrder = 3
        OnBrowse = BackupDirEditBrowse
        OnChange = SomethingChangedClick
      end
    end
    object OpPanel: TUiActivePanel
      HelpType = htKeyword
      HelpKeyword = 'OptionsOp'
      object OpConfirmLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 22
        Caption = 'Confirmations'
        FontColor = clGrayText
        FontSize = 3
        UseTitleFont = True
      end
      object OpSyncConfirmModeLbl: TUiLabel
        Left = 8
        Top = 244
        Height = 13
        Caption = 'Synchronize confirmations:'
      end
      object OpConfirmCopyEdit: TUiCheckBox
        Left = 8
        Top = 34
        Height = 17
        Caption = 'Confirm file &copy'
        TabOrder = 0
        OnClick = SomethingChangedClick
      end
      object OpConfirmMoveEdit: TUiCheckBox
        Left = 8
        Top = 55
        Height = 17
        Caption = 'Confirm file &move'
        TabOrder = 1
        OnClick = SomethingChangedClick
      end
      object OpConfirmOverwriteReadOnlyEdit: TUiCheckBox
        Left = 8
        Top = 76
        Height = 17
        Caption = 'Confirm replacing, deleting &read-only files'
        TabOrder = 2
        OnClick = SomethingChangedClick
      end
      object OpConfirmOverwriteSysFileEdit: TUiCheckBox
        Left = 8
        Top = 97
        Height = 17
        Caption = 'Confirm replacing, deleting &system files'
        TabOrder = 3
        OnClick = SomethingChangedClick
      end
      object OpConfirmOverwriteNewerEdit: TUiCheckBox
        Left = 8
        Top = 118
        Height = 17
        Caption = 'Confirm &overwriting newer files'
        TabOrder = 4
        OnClick = SomethingChangedClick
      end
      object OpConfirmMoveReplaceEdit: TUiCheckBox
        Left = 8
        Top = 139
        Height = 17
        Caption = 'Confirm replacing files during mo&ve'
        TabOrder = 5
        OnClick = SomethingChangedClick
      end
      object OpConfirmCompareEdit: TUiCheckBox
        Left = 8
        Top = 160
        Height = 17
        Caption = 'Confirm con&tent compare'
        TabOrder = 6
        OnClick = SomethingChangedClick
      end
      object OpConfirmDeleteEdit: TUiCheckBox
        Left = 8
        Top = 181
        Height = 17
        Caption = 'Confirm file &delete'
        TabOrder = 7
        OnClick = SomethingChangedClick
      end
      object OpConfirmDeleteNoSidesEdit: TUiCheckBox
        Left = 24
        Top = 202
        Height = 17
        Caption = 'Require &explicit side selection in Delete dialog'
        TabOrder = 8
        OnClick = SomethingChangedClick
      end
      object OpConfirmMergeEdit: TUiCheckBox
        Left = 8
        Top = 223
        Height = 17
        Caption = 'Confirm file mer&ge'
        TabOrder = 9
        OnClick = SomethingChangedClick
      end
      object OpSyncConfirmModePanel: TUiPanel
        Left = 0
        Top = 259
        Width = 468
        Height = 63
        BevelOuter = bvNone
        TabOrder = 10
        object OpSyncConfirmPromptEdit: TUiRadioButton
          Left = 8
          Top = 2
          Height = 17
          Caption = '&Prompt'
          TabOrder = 0
          OnClick = SomethingChangedClick
        end
        object OpSyncConfirmYesToAllEdit: TUiRadioButton
          Left = 8
          Top = 23
          Height = 17
          Caption = '&Yes to All'
          TabOrder = 1
          OnClick = SomethingChangedClick
        end
        object OpSyncConfirmNoToAllEdit: TUiRadioButton
          Left = 8
          Top = 44
          Height = 17
          Caption = '&No to All'
          TabOrder = 2
          OnClick = SomethingChangedClick
        end
      end
      object OpIncludeFilteredPanel: TUiPanel
        Left = 0
        Top = 336
        Width = 468
        Height = 98
        BevelOuter = bvNone
        TabOrder = 11
        object OpIncludeFilteredBevel: TUiBevel
          Left = 8
          Top = 0
          Width = 452
          Height = 1
          Shape = bsTopLine
        end
        object OpIncludeFilteredLbl: TUiLabel
          Left = 8
          Top = 8
          Height = 22
          Caption = 'Filtered Items'
          FontColor = clGrayText
          FontSize = 3
          UseTitleFont = True
        end
        object OpIncludeFilteredDescLbl: TUiLabel
          Left = 8
          Top = 34
          Width = 452
          Height = 26
          Caption = 'Actions performed on folders that contain items hidden by display or file filters can optionally affect the hidden items.'
          WordWrap = True
        end
        object OpIncludeFilteredEdit: TUiCheckBox
          Left = 8
          Top = 73
          Height = 17
          Caption = '&Include hidden items by default'
          TabOrder = 0
          OnClick = SomethingChangedClick
        end
      end
    end
    object ArchivePanel: TUiActivePanel
      HelpType = htKeyword
      HelpKeyword = 'OptionsArchive'
      object ArchiveLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 22
        Caption = 'Archive Types'
        FontColor = clGrayText
        FontSize = 3
        UseTitleFont = True
      end
      object ArchiveNeedsRestartLbl: TUiLabel
        Left = 8
        Top = 408
        Width = 452
        Height = 13
        Caption = 'Restart Beyond Compare to use new archive associations'
        WordWrap = True
        FontColor = clRed
      end
      object ArchiveTable: TUiListTable
        Left = 8
        Top = 34
        Width = 452
        Height = 335
        Cols.Data = ('', '')
        Cols.Strings = ('Name', 'Mask')
        ModifyColIndex = 1
        TabOrder = 0
        VertLines = True
        OnModifyApply = ArchiveTableModifyApply
      end
      object ArchiveTotalCmdrPackerBtn: TUiButton
        Left = 8
        Top = 377
        Caption = 'Add &Plug-in...'
        TabOrder = 1
        OnClick = ArchiveTotalCmdrPackerClick
        AutoSize = asLeft
      end
    end
    object CommandPanel: TUiActivePanel
      object CommandLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 22
        Caption = 'Toolbars, Shortcuts, Menus'
        FontColor = clGrayText
        FontSize = 3
        UseTitleFont = True
      end
      object CommandViewLbl: TUiLabel
        Left = 8
        Top = 34
        Height = 13
        Caption = 'Select &view:'
        FocusControl = CommandViewEdit
      end
      object CommandTableLbl: TUiLabel
        Left = 8
        Top = 80
        Height = 13
        Caption = '&Commands:'
        FocusControl = CommandTable
      end
      object CommandLongDescLbl: TUiLabel
        Left = 8
        Top = 226
        Width = 452
        Height = 13
        Caption = '%'
        WordWrap = True
      end
      object CommandShortCutLbl: TUiLabel
        Left = 8
        Top = 272
        Height = 13
        Caption = '&Shortcut:'
        FocusControl = CommandShortCutEdit
      end
      object CommandDisplayFilterModeLbl: TUiLabel
        Left = 8
        Top = 326
        Height = 13
        Caption = 'Display &filter mode:'
        FocusControl = CommandDisplayFilterModeEdit
      end
      object ToolbarShowCaptionsBevel: TUiBevel
        Left = 8
        Top = 380
        Width = 452
        Height = 1
        Shape = bsTopLine
      end
      object CommandViewEdit: TUiComboBox
        Left = 8
        Top = 51
        Width = 135
        Height = 21
        AutoDropDown = True
        Style = csDropDownList
        TabOrder = 0
        OnClick = CommandViewClick
        Images = BcImages.MainImages
        OnGetImageIndex = CommandViewEditGetImageIndex
      end
      object CommandSearchEdit: TUiSearchEdit
        Left = 336
        Top = 72
        Width = 124
        Height = 21
        TabOrder = 1
        OnChange = CommandSearchEditChange
      end
      object CommandTable: TUiListTable
        Left = 8
        Top = 97
        Width = 452
        Height = 121
        AllowColResize = True
        AllowSort = True
        Cols.Data = ('', '65', '65', '')
        Cols.Strings = ('Name', 'Menu', 'Toolbar', 'Shortcut')
        Images = BcImages.MainImages
        PopupMenu = CommandPopup
        TabOrder = 2
        VertLines = True
        OnClick = CommandTableClick
        OnCompareItems = CommandTableCompareItems
        OnGetCells = CommandTableGetCells
        OnGetChecked = CommandTableGetChecked
        OnGetHasChecked = CommandTableGetHasChecked
        OnGetImageIndex = CommandTableGetImageIndex
        OnToggleChecked = CommandTableToggleChecked
      end
      object CommandShortCutEdit: TUiShortCutEdit
        Left = 8
        Top = 289
        Width = 153
        Height = 21
        TabOrder = 3
        OnChange = CommandShortCutEditChange
        OnKeyDown = CommandShortCutEditKeyDown
      end
      object CommandShortCutRemoveBtn: TUiButton
        Left = 169
        Top = 289
        Caption = '&Remove'
        TabOrder = 4
        OnClick = CommandShortCutRemoveClick
        AutoSize = asLeft
      end
      object CommandShortCutDefaultBtn: TUiButton
        Left = 249
        Top = 289
        Caption = '&Default'
        TabOrder = 5
        OnClick = CommandShortCutDefaultClick
        AutoSize = asLeft
      end
      object CommandDisplayFilterModeEdit: TUiComboBox
        Left = 8
        Top = 343
        Width = 83
        Height = 21
        Style = csDropDownList
        TabOrder = 6
        OnChange = CommandDisplayFilterModeEditChange
      end
      object ToolbarShowCaptionsEdit: TUiCheckBox
        Left = 8
        Top = 396
        Height = 17
        Caption = '&Large buttons with text labels (all views)'
        TabOrder = 7
        OnClick = SomethingChangedClick
      end
    end
    object OpenWithPanel: TUiActivePanel
      HelpType = htKeyword
      HelpKeyword = 'OptionsOpenWith'
      object OpenWithLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 22
        Caption = '"Open With" Applications'
        FontColor = clGrayText
        FontSize = 3
        UseTitleFont = True
      end
      object OpenWithTable: TUiListTable
        Left = 8
        Top = 34
        Width = 452
        Height = 200
        Cols.Data = ('', '', '')
        Cols.Strings = ('Description', 'Command Line', 'Shortcut')
        DragMode = dmAutomatic
        TabOrder = 0
        VertLines = True
        WantReturns = True
        OnAddItem = OpenWithNewClick
        OnClick = OpenWithTableClick
        OnDblClick = OpenWithEditClick
        OnDeleteItem = OpenWithTableDeleteItem
        OnDeleteItemQuery = OpenWithTableDeleteItemQuery
        OnDragDrop = OpenWithTableDragDrop
        OnDragOver = OpenWithTableDragOver
        OnGetCells = OpenWithTableGetCells
        OnItemsDeleted = SomethingChangedClick
        OnKeyDown = OpenWithTableKeyDown
      end
      object OpenWithNewBtn: TUiBitBtn
        Left = 8
        Top = 242
        Width = 24
        Hint = 'New'
        ImageIndex = imgListAdd
        Images = BcImages.MainImages
        TabOrder = 1
        OnClick = OpenWithNewClick
      end
      object OpenWithDeleteBtn: TUiBitBtn
        Left = 32
        Top = 242
        Width = 24
        Hint = 'Delete'
        ImageIndex = imgListDelete
        Images = BcImages.MainImages
        TabOrder = 2
        OnClick = OpenWithDeleteClick
      end
      object OpenWithEditBtn: TUiBitBtn
        Left = 56
        Top = 242
        Width = 24
        Hint = 'Edit'
        ImageIndex = imgListEdit
        Images = BcImages.MainImages
        TabOrder = 3
        OnClick = OpenWithEditClick
      end
      object OpenWithCloneBtn: TUiBitBtn
        Left = 80
        Top = 242
        Width = 24
        Hint = 'Clone'
        ImageIndex = imgListClone
        Images = BcImages.MainImages
        TabOrder = 4
        OnClick = OpenWithCloneClick
      end
    end
    object TweakPanel: TUiActivePanel
      HelpType = htKeyword
      HelpKeyword = 'OptionsTweak'
      object TweakScrollBox: TUiScrollBox
        Left = 0
        Top = 0
        Width = 468
        Height = 462
        VertScrollBar.Tracking = True
        Align = alClient
        BorderStyle = bsNone
        ParentBackground = True
        TabOrder = 0
        StyleElements = [seFont, seBorder]
        object TweakBottomSpacerBevel: TUiBevel
          Left = 0
          Top = 1830
          Width = 451
          Height = 19
          Align = alTop
          Shape = bsSpacer
        end
        object CheckForUpdatesPanel: TUiPanel
          Left = 0
          Top = 0
          Width = 451
          Visible = False
          Align = alTop
          BevelOuter = bvNone
          TabOrder = 0
          object CheckForUpdatesLbl: TUiLabel
            Left = 8
            Top = 8
            Visible = False
            Caption = 'Check for Updates'
            FontColor = clGrayText
            FontSize = 3
            UseTitleFont = True
          end
          object CheckForUpdatesDayAmtDaysLbl: TUiLabel
            Left = 77
            Top = 59
            Visible = False
            Caption = 'days'
            FocusControl = CheckForUpdatesDayAmtEdit
          end
          object CheckForUpdatesLastCheckedLbl: TUiLabel
            Left = 158
            Top = 59
            Visible = False
            Caption = '%'
          end
          object CheckForUpdatesBevel: TUiBevel
            Left = 8
            Top = 91
            Width = 435
            Visible = False
            Shape = bsTopLine
          end
          object CheckForUpdatesEdit: TUiCheckBox
            Left = 8
            Top = 34
            Visible = False
            Caption = 'Check every:'
            TabOrder = 0
            OnClick = SomethingChangedClick
          end
          object CheckForUpdatesDayAmtEdit: TUiSpinEdit
            Left = 24
            Top = 55
            Width = 49
            Visible = False
            Max = 365
            MaxLength = 3
            Min = 1
            Position = 1
            TabOrder = 1
            OnChange = SomethingChangedClick
          end
        end
        object TextTweakPanel: TUiPanel
          Left = 0
          Top = 92
          Width = 451
          Height = 320
          Align = alTop
          BevelOuter = bvNone
          TabOrder = 1
          object TextTweakLbl: TUiLabel
            Left = 8
            Top = 8
            Height = 22
            Caption = 'Editor Display'
            FontColor = clGrayText
            FontSize = 3
            UseTitleFont = True
          end
          object TextItemSpacingLbl: TUiLabel
            Left = 8
            Top = 122
            Height = 13
            Caption = 'Extra line spacing:'
            FocusControl = TextItemSpacingEdit
          end
          object TextItemSpacingPixelsLbl: TUiLabel
            Left = 61
            Top = 143
            Height = 13
            Caption = 'pixels'
            FocusControl = TextItemSpacingEdit
          end
          object TextRightMarginOffsetLbl: TUiLabel
            Left = 8
            Top = 168
            Height = 13
            Caption = 'Show column line at:'
            FocusControl = TextRightMarginOffsetEdit
            Transparent = True
          end
          object DimPctLbl: TUiLabel
            Left = 8
            Top = 214
            Height = 13
            Caption = 'Dim inactive pane by:'
            FocusControl = DimPctEdit
          end
          object DimPctPctLbl: TUiLabel
            Left = 61
            Top = 235
            Height = 13
            Caption = '%'
            FocusControl = DimPctEdit
          end
          object TextInputFontLbl: TUiLabel
            Left = 105
            Top = 286
            Width = 338
            Height = 13
            AutoSize = False
            Caption = 'Sample Text'
          end
          object TextTweakBevel: TUiBevel
            Left = 8
            Top = 319
            Width = 435
            Height = 1
            Shape = bsTopLine
          end
          object TextSyntaxDiffsEdit: TUiCheckBox
            Left = 8
            Top = 34
            Height = 17
            Caption = 'Show syntax highlighting on difference lines'
            TabOrder = 0
            OnClick = SomethingChangedClick
          end
          object TextCrosshatchBeyondEOFEdit: TUiCheckBox
            Left = 8
            Top = 55
            Height = 17
            Caption = 'Use crosshatching for lines beyond the end of file'
            TabOrder = 1
            OnClick = SomethingChangedClick
          end
          object TextRightGutterEdit: TUiCheckBox
            Left = 8
            Top = 76
            Height = 17
            Caption = 'Right side gutter for left editor (compare only)'
            TabOrder = 2
            OnClick = SomethingChangedClick
          end
          object TextUseOrphanColorEdit: TUiCheckBox
            Left = 8
            Top = 97
            Height = 17
            Caption = 'Use orphan color'
            TabOrder = 3
            OnClick = SomethingChangedClick
          end
          object TextItemSpacingEdit: TUiSpinEdit
            Left = 8
            Top = 139
            Width = 49
            Height = 21
            Max = 6
            MaxLength = 2
            Min = -6
            TabOrder = 4
            OnChange = SomethingChangedClick
          end
          object TextRightMarginOffsetEdit: TUiSpinEdit
            Left = 8
            Top = 185
            Width = 49
            Height = 21
            TabOrder = 5
            OnChange = SomethingChangedClick
          end
          object DimPctEdit: TUiSpinEdit
            Left = 8
            Top = 231
            Width = 49
            Height = 21
            Increment = 5
            Max = 100
            MaxLength = 3
            TabOrder = 6
            OnChange = SomethingChangedClick
          end
          object TextUseInputFontEdit: TUiCheckBox
            Left = 8
            Top = 260
            Height = 17
            Caption = 'Use different font for merge input panes:'
            TabOrder = 7
            OnClick = SomethingChangedClick
          end
          object TextInputFontBtn: TUiButton
            Left = 24
            Top = 281
            Caption = 'Font...'
            TabOrder = 8
            OnClick = TextInputFontClick
            AutoSize = asLeft
          end
        end
        object OpTweakPanel: TUiPanel
          Left = 0
          Top = 412
          Width = 451
          Height = 243
          Align = alTop
          BevelOuter = bvNone
          TabOrder = 2
          object OpTweakLbl: TUiLabel
            Left = 8
            Top = 8
            Height = 22
            Caption = 'File Operations'
            FontColor = clGrayText
            FontSize = 3
            UseTitleFont = True
          end
          object FileComparePriorityLbl: TUiLabel
            Left = 8
            Top = 143
            Height = 13
            Caption = 'Comparison priority:'
            FocusControl = FileComparePriorityEdit
          end
          object FileBinaryCompareBufSizeLbl: TUiLabel
            Left = 8
            Top = 189
            Height = 13
            Caption = 'Buffer size for binary compare:'
            FocusControl = FileBinaryCompareBufSizeEdit
          end
          object FileBinaryCompareBufSizeBytesLbl: TUiLabel
            Left = 93
            Top = 210
            Height = 13
            Caption = 'bytes'
            FocusControl = FileBinaryCompareBufSizeEdit
          end
          object OpTweakBevel: TUiBevel
            Left = 8
            Top = 242
            Width = 435
            Height = 1
            Shape = bsTopLine
          end
          object OpBeepWhenFinishedEdit: TUiCheckBox
            Left = 8
            Top = 34
            Height = 17
            Caption = 'Beep after long file operations'
            TabOrder = 0
            OnClick = SomethingChangedClick
          end
          object OpClearCDReadOnlyEdit: TUiCheckBox
            Left = 8
            Top = 55
            Height = 17
            Caption = 'Remove read-only flag when copying from a CD or DVD'
            TabOrder = 1
            OnClick = SomethingChangedClick
          end
          object FileCheckForChangesEdit: TUiCheckBox
            Left = 8
            Top = 76
            Height = 17
            Caption = 'Check for files changed on disk'
            TabOrder = 2
            OnClick = SomethingChangedClick
          end
          object FileCheckForChangesAutoReloadEdit: TUiCheckBox
            Left = 24
            Top = 97
            Height = 17
            Caption = 'Automatically reload unless changes will be discarded'
            TabOrder = 3
            OnClick = SomethingChangedClick
          end
          object UseIPv6Edit: TUiCheckBox
            Left = 8
            Top = 118
            Height = 17
            Caption = 'Use IPv6 when available'
            TabOrder = 4
            OnClick = SomethingChangedClick
          end
          object FileComparePriorityEdit: TUiComboBox
            Left = 8
            Top = 160
            Width = 67
            Height = 21
            Style = csDropDownList
            TabOrder = 5
            OnChange = SomethingChangedClick
            Items.Strings = ('Low', 'Normal', 'High')
          end
          object FileBinaryCompareBufSizeEdit: TUiSpinEdit
            Left = 8
            Top = 206
            Width = 81
            Height = 21
            Min = 1
            Position = 1
            TabOrder = 6
            OnChange = SomethingChangedClick
          end
        end
        object HomePanel: TUiPanel
          Left = 0
          Top = 655
          Width = 451
          Height = 67
          Align = alTop
          BevelOuter = bvNone
          TabOrder = 3
          object HomeLbl: TUiLabel
            Left = 8
            Top = 8
            Height = 22
            Caption = 'Home View'
            FontColor = clGrayText
            FontSize = 3
            UseTitleFont = True
          end
          object HomeBevel: TUiBevel
            Left = 8
            Top = 66
            Width = 435
            Height = 1
            Shape = bsTopLine
          end
          object HomeMRUSessionOnlyEdit: TUiCheckBox
            Left = 8
            Top = 34
            Height = 17
            Caption = 'Sticky session selection'
            TabOrder = 0
            OnClick = SomethingChangedClick
          end
        end
        object InterfacePanel: TUiPanel
          Left = 0
          Top = 722
          Width = 451
          Height = 214
          Align = alTop
          BevelOuter = bvNone
          TabOrder = 4
          object InterfaceLbl: TUiLabel
            Left = 8
            Top = 8
            Height = 22
            Caption = 'Interface'
            FontColor = clGrayText
            FontSize = 3
            UseTitleFont = True
          end
          object ThumbnailScrollLbl: TUiLabel
            Left = 8
            Top = 143
            Height = 13
            Caption = 'For thumbnail view on large files:'
          end
          object InterfaceBevel: TUiBevel
            Left = 8
            Top = 213
            Width = 435
            Height = 1
            Shape = bsTopLine
          end
          object ShowHintsEdit: TUiCheckBox
            Left = 8
            Top = 34
            Height = 17
            Caption = 'Show hints for toolbar buttons, etc.'
            TabOrder = 0
            OnClick = SomethingChangedClick
          end
          object HintShortCutsEdit: TUiCheckBox
            Left = 24
            Top = 55
            Height = 17
            Caption = 'Show keyboard shortcut in hints'
            TabOrder = 1
            OnClick = SomethingChangedClick
          end
          object FileEscCloseEdit: TUiCheckBox
            Left = 8
            Top = 76
            Height = 17
            Caption = 'ESC key closes file views'
            TabOrder = 2
            OnClick = SomethingChangedClick
          end
          object FileVertScrollBarSingleEdit: TUiCheckBox
            Left = 8
            Top = 97
            Height = 17
            Caption = 'Single vertical scrollbar'
            TabOrder = 3
            OnClick = SomethingChangedClick
          end
          object FileUseLeftRatioEdit: TUiCheckBox
            Left = 8
            Top = 118
            Height = 17
            Caption = 'Sticky splitter position'
            TabOrder = 4
            OnClick = SomethingChangedClick
          end
          object ThumbnailScrollPanel: TUiPanel
            Left = 0
            Top = 158
            Width = 451
            Height = 42
            BevelOuter = bvNone
            TabOrder = 5
            object ThumbnailCompressEdit: TUiRadioButton
              Left = 8
              Top = 2
              Height = 17
              Caption = 'Compress to fit'
              TabOrder = 0
              OnClick = SomethingChangedClick
            end
            object ThumbnailScrollEdit: TUiRadioButton
              Left = 8
              Top = 23
              Height = 17
              Caption = 'Allow scrolling'
              TabOrder = 1
              OnClick = SomethingChangedClick
            end
          end
        end
        object LogPanel: TUiPanel
          Left = 0
          Top = 936
          Width = 451
          Height = 260
          Align = alTop
          BevelOuter = bvNone
          TabOrder = 5
          object LogLbl: TUiLabel
            Left = 8
            Top = 8
            Height = 22
            Caption = 'Log Panel'
            FontColor = clGrayText
            FontSize = 3
            UseTitleFont = True
          end
          object LogIncludeLbl: TUiLabel
            Left = 8
            Top = 34
            Height = 13
            Caption = 'Include:'
          end
          object LogMaxSizeLbl: TUiLabel
            Left = 8
            Top = 160
            Height = 13
            Caption = 'Display up to:'
            FocusControl = LogMaxSizeEdit
          end
          object LogMaxSizeMessagesLbl: TUiLabel
            Left = 101
            Top = 181
            Height = 13
            Caption = 'messages'
            FocusControl = LogMaxSizeEdit
          end
          object LogAutoSaveFilenameLbl: TUiLabel
            Left = 8
            Top = 206
            Height = 13
            Caption = 'Automatically save messages to file:'
            FocusControl = LogAutoSaveFilenameEdit
          end
          object LogBevel: TUiBevel
            Left = 8
            Top = 259
            Width = 435
            Height = 1
            Shape = bsTopLine
          end
          object LogIncludeOpSummaryEdit: TUiCheckBox
            Left = 8
            Top = 51
            Height = 17
            Caption = 'Operation summaries'
            TabOrder = 0
            OnClick = SomethingChangedClick
          end
          object LogIncludeOpDetailsEdit: TUiCheckBox
            Left = 8
            Top = 72
            Height = 17
            Caption = 'Operation details'
            TabOrder = 1
            OnClick = SomethingChangedClick
          end
          object LogIncludeWarningEdit: TUiCheckBox
            Left = 8
            Top = 93
            Height = 17
            Caption = 'Warnings'
            TabOrder = 2
            OnClick = SomethingChangedClick
          end
          object LogIncludeConnectionEdit: TUiCheckBox
            Left = 8
            Top = 114
            Height = 17
            Caption = 'FTP trace'
            TabOrder = 3
            OnClick = SomethingChangedClick
          end
          object LogIncludeDebugEdit: TUiCheckBox
            Left = 8
            Top = 135
            Height = 17
            Caption = 'Debug messages'
            TabOrder = 4
            OnClick = SomethingChangedClick
          end
          object LogMaxSizeEdit: TUiSpinMRUEdit
            Left = 8
            Top = 177
            Width = 89
            Height = 21
            Increment = 1000
            Min = 1000
            Position = 1000000
            TabOrder = 5
            OnChange = SomethingChangedClick
          end
          object LogAutoSaveFilenameEdit: TUiSpecBar
            Left = 8
            Top = 223
            Width = 435
            TabOrder = 6
            OnBrowse = LogAutoSaveFilenameEditBrowse
            OnChange = SomethingChangedClick
          end
        end
        object MetricsPanel: TUiPanel
          Left = 0
          Top = 1196
          Width = 451
          Height = 187
          Align = alTop
          BevelOuter = bvNone
          TabOrder = 6
          object MetricsLbl: TUiLabel
            Left = 8
            Top = 8
            Height = 22
            Caption = 'Metrics'
            FontColor = clGrayText
            FontSize = 3
            UseTitleFont = True
          end
          object SessionAutoSavedCapacityLbl: TUiLabel
            Left = 61
            Top = 38
            Height = 13
            Caption = 'max auto-saved sessions'
            FocusControl = SessionAutoSavedCapacityEdit
          end
          object MRUCapacityLbl: TUiLabel
            Left = 61
            Top = 67
            Height = 13
            Caption = 'max most recently used (MRU) items'
            FocusControl = MRUCapacityEdit
          end
          object HintPauseLbl: TUiLabel
            Left = 101
            Top = 96
            Height = 13
            Caption = 'milliseconds before help hint appears'
            FocusControl = HintPauseEdit
          end
          object HintHidePauseLbl: TUiLabel
            Left = 101
            Top = 125
            Height = 13
            Caption = 'milliseconds before help hint disappears'
            FocusControl = HintHidePauseEdit
          end
          object SearchTimerIntervalLbl: TUiLabel
            Left = 101
            Top = 154
            Height = 13
            Caption = 'milliseconds before incremental search resets'
            FocusControl = SearchTimerIntervalEdit
          end
          object MetricsBevel: TUiBevel
            Left = 8
            Top = 186
            Width = 435
            Height = 1
            Shape = bsTopLine
          end
          object SessionAutoSavedCapacityEdit: TUiSpinMRUEdit
            Left = 8
            Top = 34
            Width = 49
            Height = 21
            TabOrder = 0
            OnChange = SomethingChangedClick
          end
          object MRUCapacityEdit: TUiSpinMRUEdit
            Left = 8
            Top = 63
            Width = 49
            Height = 21
            Min = 1
            Position = 1
            TabOrder = 1
            OnChange = SomethingChangedClick
          end
          object HintPauseEdit: TUiSpinEdit
            Left = 8
            Top = 92
            Width = 89
            Height = 21
            TabOrder = 2
            OnChange = SomethingChangedClick
          end
          object HintHidePauseEdit: TUiSpinEdit
            Left = 8
            Top = 121
            Width = 89
            Height = 21
            TabOrder = 3
            OnChange = SomethingChangedClick
          end
          object SearchTimerIntervalEdit: TUiSpinEdit
            Left = 8
            Top = 150
            Width = 89
            Height = 21
            TabOrder = 4
            OnChange = SomethingChangedClick
          end
        end
        object FilterPresetPanel: TUiPanel
          Left = 0
          Top = 1383
          Width = 451
          Height = 242
          Align = alTop
          BevelOuter = bvNone
          TabOrder = 7
          object FilterPresetLbl: TUiLabel
            Left = 8
            Top = 8
            Height = 22
            Caption = 'Name Filter Presets'
            FontColor = clGrayText
            FontSize = 3
            UseTitleFont = True
          end
          object FilterPresetBevel: TUiBevel
            Left = 8
            Top = 241
            Width = 435
            Height = 1
            Shape = bsTopLine
          end
          object FilterPresetTable: TUiListTable
            Left = 8
            Top = 34
            Width = 435
            Height = 161
            Cols.Data = ('', '')
            Cols.Strings = ('Name', 'Mask')
            DragMode = dmAutomatic
            TabOrder = 0
            VertLines = True
            WantReturns = True
            OnAddItem = FilterPresetNewClick
            OnClick = FilterPresetTableClick
            OnDblClick = FilterPresetEditClick
            OnDeleteItemQuery = FilterPresetTableDeleteItemQuery
            OnDragDrop = FilterPresetTableDragDrop
            OnDragOver = FilterPresetTableDragOver
            OnGetCells = FilterPresetTableGetCells
            OnItemsDeleted = SomethingChangedClick
            OnKeyDown = FilterPresetTableKeyDown
          end
          object FilterPresetNewBtn: TUiBitBtn
            Left = 8
            Top = 203
            Width = 24
            Hint = 'New'
            ImageIndex = imgListAdd
            Images = BcImages.MainImages
            TabOrder = 1
            OnClick = FilterPresetNewClick
          end
          object FilterPresetDeleteBtn: TUiBitBtn
            Left = 32
            Top = 203
            Width = 24
            Hint = 'Delete'
            ImageIndex = imgListDelete
            Images = BcImages.MainImages
            TabOrder = 2
            OnClick = FilterPresetDeleteClick
          end
          object FilterPresetEditBtn: TUiBitBtn
            Left = 56
            Top = 203
            Width = 24
            Hint = 'Edit'
            ImageIndex = imgListEdit
            Images = BcImages.MainImages
            TabOrder = 3
            OnClick = FilterPresetEditClick
          end
        end
        object ScriptPanel: TUiPanel
          Left = 0
          Top = 1625
          Width = 451
          Height = 134
          Align = alTop
          BevelOuter = bvNone
          TabOrder = 8
          object ScriptLbl: TUiLabel
            Left = 8
            Top = 8
            Height = 22
            Caption = 'Scripts'
            FontColor = clGrayText
            FontSize = 3
            UseTitleFont = True
          end
          object ScriptSharedDirLbl: TUiLabel
            Left = 8
            Top = 80
            Height = 13
            Caption = 'Shared scripts folder:'
            FocusControl = ScriptSharedDirEdit
          end
          object ScriptBevel: TUiBevel
            Left = 8
            Top = 133
            Width = 435
            Height = 1
            Shape = bsTopLine
          end
          object ScriptBeepWhenFinishedEdit: TUiCheckBox
            Left = 8
            Top = 34
            Height = 17
            Caption = 'Beep when finished'
            TabOrder = 0
            OnClick = SomethingChangedClick
          end
          object ScriptCloseWhenFinishedEdit: TUiCheckBox
            Left = 8
            Top = 55
            Height = 17
            Caption = 'Close when finished'
            TabOrder = 1
            OnClick = SomethingChangedClick
          end
          object ScriptSharedDirEdit: TUiSpecBar
            Left = 8
            Top = 97
            Width = 435
            AutoCompleteEx = acDirs
            TabOrder = 2
            OnBrowse = ScriptSharedDirEditBrowse
            OnChange = SomethingChangedClick
          end
        end
        object SharedSessionPanel: TUiPanel
          Left = 0
          Top = 1759
          Width = 451
          Height = 71
          Align = alTop
          BevelOuter = bvNone
          TabOrder = 9
          object SharedSessionLbl: TUiLabel
            Left = 8
            Top = 8
            Height = 22
            Caption = 'Shared Sessions File'
            FontColor = clGrayText
            FontSize = 3
            UseTitleFont = True
          end
          object SharedSessionBevel: TUiBevel
            Left = 8
            Top = 70
            Width = 435
            Height = 1
            Shape = bsTopLine
          end
          object SharedSessionFilenameEdit: TUiSpecBar
            Left = 8
            Top = 34
            Width = 435
            TabOrder = 0
            OnBrowse = SharedSessionFilenameEditBrowse
            OnChange = SomethingChangedClick
          end
        end
      end
    end
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 462
    Width = 657
    ParentBackground = False
    ParentColor = True
    TabOrder = 2
    OnPaint = BtnPanelPaint
    object OkBtn: TUiOkBtn
      OnClick = ApplyClick
    end
    object CancelBtn: TUiCancelBtn
      OnClick = CancelClick
    end
    object ApplyBtn: TUiAdvancedBtn
      Caption = '&Apply'
      OnClick = ApplyClick
    end
  end
  object CommandPopup: TUiPopupMenu
    Left = 8
    Top = 8
    object CommandMenuAllowedAllItem: TUiMenuItem
      Caption = 'Show All in Menu'
      OnClick = CommandMenuAllowedAllClick
    end
    object CommandToolbarAllowedAllItem: TUiMenuItem
      Caption = 'Show All on Toolbar'
      OnClick = CommandToolbarAllowedAllClick
    end
  end
end
