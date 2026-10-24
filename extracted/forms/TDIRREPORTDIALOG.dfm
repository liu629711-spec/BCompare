object DirReportDialog: TDirReportDialog
  Caption = 'Folder Compare Report'
  PixelsPerInch = 96
  TextHeight = 13
  object LayoutListBox: TUiListBox
    Items.Strings = ('Side-by-side', 'Summary', 'XML Dump')
  end
  object OptionsPanel: TUiPanel
    object BasicPanel: TUiPanel
      Height = 0
    end
    object DisplayFilterPanel: TUiPanel
      Top = 0
    end
    object LayoutPanelView: TUiActivePanelView
      Height = 0
      Align = alNone
    end
    object ColsPanel: TUiPanel
      Left = 0
      Top = 29
      Width = 385
      Height = 76
      Align = alTop
      BevelOuter = bvNone
      TabOrder = 3
      object ColsLbl: TUiLabel
        Left = 0
        Top = 0
        Height = 13
        Caption = 'Col&umns:'
      end
      object VcsStatusEdit: TUiCheckBox
        Left = 0
        Top = 17
        Height = 17
        Caption = 'Status'
        TabOrder = 0
        OnClick = SomethingChangedClick
      end
      object VcsVersionEdit: TUiCheckBox
        Left = 0
        Top = 34
        Height = 17
        Caption = 'Revision'
        TabOrder = 1
        OnClick = SomethingChangedClick
      end
      object VersionEdit: TUiCheckBox
        Left = 0
        Top = 51
        Height = 17
        Caption = 'Version'
        TabOrder = 2
        OnClick = SomethingChangedClick
      end
      object SizeEdit: TUiCheckBox
        Left = 131
        Top = 17
        Height = 17
        Caption = 'Size'
        TabOrder = 3
        OnClick = SomethingChangedClick
      end
      object CRCEdit: TUiCheckBox
        Left = 131
        Top = 34
        Height = 17
        Caption = 'CRC'
        TabOrder = 4
        OnClick = SomethingChangedClick
      end
      object ModifiedEdit: TUiCheckBox
        Left = 131
        Top = 51
        Height = 17
        Caption = 'Modified'
        TabOrder = 5
        OnClick = SomethingChangedClick
      end
      object AttributesEdit: TUiCheckBox
        Left = 262
        Top = 17
        Height = 17
        Caption = 'Attributes'
        TabOrder = 6
        OnClick = SomethingChangedClick
      end
      object UnixOwnerEdit: TUiCheckBox
        Left = 262
        Top = 34
        Height = 17
        Caption = 'Owner'
        TabOrder = 7
        OnClick = SomethingChangedClick
      end
      object UnixGroupEdit: TUiCheckBox
        Left = 262
        Top = 51
        Height = 17
        Caption = 'Group'
        TabOrder = 8
        OnClick = SomethingChangedClick
      end
    end
  end
  object OutputPanel: TUiPanel
    object OutputPanelView: TUiActivePanelView
      object HTMLPanel: TUiActivePanel
        object CompoundEdit: TUiCheckBox
          Left = 0
          Top = 113
          Height = 17
          Caption = 'Include links to &file reports'
          TabOrder = 2
          OnClick = SomethingChangedClick
        end
      end
    end
  end
end
