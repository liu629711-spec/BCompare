object SourceControlManagerDialog: TSourceControlManagerDialog
  HelpType = htKeyword
  HelpKeyword = 'DlgSourceControlManager'
  BorderIcons = [biSystemMenu, biHelp]
  BorderStyle = bsSizeable
  Caption = 'Source Control Integration'
  ClientHeight = 590
  ClientWidth = 632
  Constraints.MinHeight = 233
  Constraints.MinWidth = 188
  OnResize = FormResize
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object BottomLineBevel: TUiBevel
    Left = 0
    Top = 540
    Width = 632
    Height = 11
    Align = alBottom
    Shape = bsBottomLine
  end
  object Panel: TUiPanel
    Left = 0
    Top = 0
    Width = 632
    Height = 540
    Align = alClient
    BevelOuter = bvNone
    TabOrder = 0
    object PathLbl: TUiLabel
      Left = 8
      Top = 8
      Height = 13
      Caption = 'Enter &path to add a new association:'
      FocusControl = PathEdit
    end
    object ListLbl: TUiLabel
      Left = 8
      Top = 54
      Height = 13
      Caption = '&Existing associations:'
      FocusControl = ListTable
    end
    object PathEdit: TUiSpecBar
      Left = 8
      Top = 25
      Width = 535
      AutoCompleteEx = acDirs
      TabOrder = 0
      OnBrowse = PathEditBrowse
      OnChange = SomethingChangedClick
    end
    object AddBtn: TUiButton
      Left = 551
      Top = 25
      Caption = '&Add...'
      TabOrder = 1
      OnClick = AddClick
      AutoSize = asRight
    end
    object ListTable: TUiListTable
      Left = 8
      Top = 71
      Width = 616
      Height = 413
      Cols.Data = ('', '')
      Cols.Strings = ('Folder', 'Project')
      TabOrder = 2
      VertLines = True
      WantReturns = True
      OnClick = SomethingChangedClick
      OnDblClick = ConfigClick
      OnDeleteItem = ListTableDeleteItem
      OnDeleteItemQuery = ListTableDeleteItemQuery
      OnGetCells = ListTableGetCells
      OnItemsDeleted = SomethingChangedClick
    end
    object RemoveBtn: TUiButton
      Left = 467
      Top = 492
      Caption = '&Remove...'
      TabOrder = 3
      OnClick = RemoveClick
      AutoSize = asRight
    end
    object ConfigBtn: TUiButton
      Left = 548
      Top = 492
      Width = 76
      Caption = '&Configure...'
      TabOrder = 4
      OnClick = ConfigClick
      AutoSize = asRight
    end
    object ShowSilentCheckOutEdit: TUiCheckBox
      Left = 8
      Top = 523
      Height = 17
      Caption = '&Display silent check out command in menus'
      TabOrder = 5
      OnClick = ShowSilentCheckOutClick
    end
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 551
    Width = 632
    TabOrder = 1
    SizeGripper = True
    object CloseBtn: TUiCloseBtn
    end
  end
end
