object OpCompareResultsDialog: TOpCompareResultsDialog
  BorderStyle = bsSizeable
  Caption = '%'
  ClientHeight = 343
  ClientWidth = 377
  Constraints.MinHeight = 75
  Constraints.MinWidth = 105
  OnClose = FormClose
  OnCreate = FormCreate
  OnDestroy = FormDestroy
  OnKeyPress = FormKeyPress
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object TreeView: TUiSimpleTreeView
    Left = 0
    Top = 0
    Width = 377
    Height = 324
    Align = alClient
    Images = BcImages.ContentImages
    ShowLeafImage = True
    TabOrder = 0
    OnDblClick = TreeViewDblClick
  end
  object StatusBar: TUiStatusBar
    Left = 0
    Top = 324
    Width = 377
    Height = 19
    Panels = <
    >
    SimplePanel = True
    SimpleText = 'Double-click a file to open it in the associated view.'
  end
end
